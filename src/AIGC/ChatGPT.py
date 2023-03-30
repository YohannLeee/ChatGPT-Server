import asyncio
import json
import logging
import os
import sys
import pathlib
sys.path.append(
    pathlib.Path(__file__).parent.parent.as_posix()
)
from typing import AsyncGenerator, Dict, Generator, Text, Tuple

import openai
import requests
import tiktoken
import aiohttp

from library.utils import get_filtered_keys_from_object, CFG
from settings import conf

# openai.api_key = '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'
log = logging.getLogger("app.chat")

class Chatbot:
    """
    Official ChatGPT API
    excerpt from https://github.com/acheong08/ChatGPT.git
    """

    def __init__(
        self,
        api_key: str,
        engine: str = os.environ.get("GPT_ENGINE") or "gpt-3.5-turbo",
        proxy: str = '',
        max_tokens: int = 3000,
        temperature: float = 0.5,
        top_p: float = 1.0,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        reply_count: int = 1,
        system_prompt: str = "You are ChatGPT, a large language model trained by OpenAI. Respond conversationally",
        stream: bool = False,
    ) -> None:
        """
        Initialize Chatbot with API key (from https://platform.openai.com/account/api-keys)
        """
        if not api_key:
            api_key = CFG.C['ChatGPT']['API_KEY']

        self.engine = engine
        # self.session = requests.Session()
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.reply_count = reply_count
        self.stream = stream

        if not proxy:
            proxy = CFG.C['ChatGPT']['PROXY']

        self.proxy = proxy
            # self.session.proxies = {
            #     "http": proxy,
            #     "https": proxy,
            # }
        log.debug(f"Proxy: {self.proxy}")
        self.conversation = {}
        self.new_user()
        if max_tokens > 4000:
            raise Exception("Max tokens cannot be greater than 4000")

        if self.get_token_count("default") > self.max_tokens:
            raise Exception("System prompt is too long")
        self.load(CFG.C['ChatGPT']['CONF_FP'], 'not', 'api_key')

    def add_to_conversation(
        self,
        message: str,
        role: str,
        convo_id: str = "default",
    ) -> None:
        """
        Add a message to the conversation
        """
        if not self.conversation[convo_id]['use_history']:
            self.reset(convo_id)
            # self.conversation[convo_id]['history'] = [dict(role= role, content= message)]
        self.conversation[convo_id]['history'].append(dict(role= role, content= message))

    def __truncate_conversation(self, convo_id: str = "default") -> None:
        """
        Truncate the conversation
        """
        while True:
            if (
                self.get_token_count(convo_id) > self.max_tokens
                and len(self.conversation[convo_id]['history']) > 1
            ):
                # Don't remove the first message
                self.conversation[convo_id]['history'].pop(1)
            else:
                break

    # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    def get_token_count(self, convo_id: str = "default") -> int:
        """
        Get token count
        """
        if self.engine not in ["gpt-3.5-turbo", "gpt-3.5-turbo-0301"]:
            raise NotImplementedError("Unsupported engine {self.engine}")

        encoding = tiktoken.encoding_for_model(self.engine)

        num_tokens = 0
        for message in self.conversation[convo_id]['history']:
            # every message follows <im_start>{role/name}\n{content}<im_end>\n
            num_tokens += 4
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens

    def get_max_tokens(self, convo_id: str) -> int:
        """
        Get max tokens
        """
        return self.max_tokens - self.get_token_count(convo_id)

    def ask_stream(
        self,
        prompt: str,
        role: str = "user",
        convo_id: str = "default",
        **kwargs,
    ) -> Generator:
        """
        Ask a question
        """
        # Make conversation if it doesn't exist
        if convo_id not in self.conversation:
            self.new_user(convo_id=convo_id, system_prompt=self.system_prompt)
        self.add_to_conversation(prompt, "user", convo_id=convo_id)
        _stream = kwargs.get('stream', True)
        self.__truncate_conversation(convo_id=convo_id)
        payload = {
                "model": self.engine,
                "messages": self.conversation[convo_id]['history'],
                "stream": _stream,
                # kwargs
                "temperature": kwargs.get("temperature", self.temperature),
                "top_p": kwargs.get("top_p", self.top_p),
                "presence_penalty": kwargs.get(
                    "presence_penalty",
                    self.presence_penalty,
                ),
                "frequency_penalty": kwargs.get(
                    "frequency_penalty",
                    self.frequency_penalty,
                ),
                "n": kwargs.get("n", self.reply_count),
                "user": role,
                "max_tokens": self.get_max_tokens(convo_id=convo_id),
            }
        log.debug(f"Request payload: {payload}")
        # Get response
        try_index = 0
        while try_index < 3:
            try:
                response = requests.post(
                    os.environ.get("API_URL") or "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {kwargs.get('api_key', self.api_key)}"},
                    json= payload,
                    stream = _stream,
                    verify = False,
                    proxies = {
                        "http": self.proxy,
                        "https": self.proxy,
                    } if self.proxy else None
                )
                break
            except requests.exceptions.ProxyError as e:
                log.exception(e)
                log.info(f"Proxy: {self.proxy}")
            finally:
                try_index += 1
                if try_index == 3:
                    return f"Error: {e}"

        match response.status_code:
            case 401:
                raise Exception(f"Error: {response.status_code} {response.reason} {response.text}\n API_KEY: {kwargs.get('api_key', self.api_key)}")
            case 200:
                pass
            case _:
               raise Exception(
                f"Error: {response.status_code} {response.reason} {response.text}",
            ) 
            
        if _stream:
            response_role: str = ''
            full_response: str = ""
            # log.debug(f"{response.text=}")
            for line in response.iter_lines():
                if not line:
                    continue
                # Remove "data: "
                line = line.decode("utf-8")[6:]
                if line == "[DONE]":
                    break
                resp: dict = json.loads(line)
                choices = resp.get("choices") # type: ignore
                if not choices:
                    continue
                delta = choices[0].get("delta")
                if not delta:
                    continue
                if "role" in delta:
                    response_role = delta["role"]
                if "content" in delta:
                    content = delta["content"]
                    full_response += content
                    yield content
            # log.debug(f"{response.text=}")
        else:
            resp: dict = json.loads(response.content)
            # TODO save usage info
            usage: dict = resp['usage']
            choices: dict = resp['choices'][0]
            response_role = choices['message']['role']
            full_response = choices['message']['content'].strip()
            self.calculate_token(convo_id=convo_id, usage= usage)

        if self.conversation[convo_id]['use_history']:
            self.add_to_conversation(full_response, response_role, convo_id=convo_id)
        if not _stream:
            yield full_response

    async def aask_stream(
        self,
        prompt: str,
        role: str = "user",
        convo_id: str = "default",
        **kwargs,
    ) -> AsyncGenerator:
        """
        Ask a question
        """
        # Make conversation if it doesn't exist
        if convo_id not in self.conversation:
            self.new_user(convo_id=convo_id, system_prompt=self.system_prompt)
        self.add_to_conversation(prompt, "user", convo_id=convo_id)
        _stream = kwargs.get('stream', True)
        self.__truncate_conversation(convo_id=convo_id)
        payload = {
                "model": self.engine,
                "messages": self.conversation[convo_id]['history'],
                "stream": _stream,
                # kwargs
                "temperature": kwargs.get("temperature", self.temperature),
                "top_p": kwargs.get("top_p", self.top_p),
                "presence_penalty": kwargs.get(
                    "presence_penalty",
                    self.presence_penalty,
                ),
                "frequency_penalty": kwargs.get(
                    "frequency_penalty",
                    self.frequency_penalty,
                ),
                "n": kwargs.get("n", self.reply_count),
                "user": role,
                "max_tokens": self.get_max_tokens(convo_id=convo_id),
            }
        log.debug(f"Request payload: {payload}")
        # Get response
        try_index = 0
        response: aiohttp.ClientResponse
        while try_index < 3:
            try:
                async with aiohttp.ClientSession() as ss:
                    response = await ss.post(
                        os.environ.get("API_URL") or "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {kwargs.get('api_key', self.api_key)}"},
                        json= payload,
                        ssl = False,
                        proxy = self.proxy
                    )
                break
            except requests.exceptions.ProxyError as e:
                log.exception(e)
                log.info(f"Proxy: {self.proxy}")
            finally:
                try_index += 1
                if try_index == 3:
                    yield f"Error: {e}"
                    return 

        match response.status:
            case 401:
                raise Exception(f"Error: {response.status} {response.reason} {await response.text()}\n API_KEY: {kwargs.get('api_key', self.api_key)}")
            case 200:
                pass
            case _:
               raise Exception(
                f"Error: {response.status} {response.reason} {await response.text()}",
            ) 
            

        response_role: str = ''
        full_response: str = ""
        # log.debug(f"{response.text=}")
        # async for line, _ in response.content.iter_chunks():
        async for line in response.content:
            print(f"{line=}")
            if not line or not line.startswith(b'data: '):
                continue
            # Remove "data: "
            line = line.decode("utf-8")[6:]
            if line == "[DONE]":
                break
            # print(f"{line=}\n{response.headers=}")
            resp: dict = json.loads(line)
            choices = resp.get("choices") # type: ignore
            if not choices:
                continue
            delta = choices[0].get("delta")
            if not delta:
                continue
            if "role" in delta:
                response_role = delta["role"]
            if "content" in delta:
                content = delta["content"]
                full_response += content
                print(f"Yielding {content=}")
                yield content

        if self.conversation[convo_id]['use_history']:
            self.add_to_conversation(full_response, response_role, convo_id=convo_id)

    def ask(
        self,
        prompt: str,
        role: str = "user",
        convo_id: str = "default",
        stream: bool = False,
        **kwargs,
    ) -> str:
        """
        Non-streaming ask
        """
        full_response = self.ask_stream(
            prompt=prompt,
            role=role,
            convo_id=convo_id,
            stream = stream,
            **kwargs,
        )
        # print(dir(full_response))
        return next(full_response)
    
    async def aask(
        self,
        prompt: str,
        role: str = "user",
        convo_id: str = "default",
        msg_id: str = '1',
        **kwargs,
    ) -> tuple[str, str]:
        """
        Non-streaming ask
        """
        # Make conversation if it doesn't exist
        if convo_id not in self.conversation:
            self.new_user(convo_id=convo_id, system_prompt=self.system_prompt)
        self.add_to_conversation(prompt, "user", convo_id=convo_id)
        self.__truncate_conversation(convo_id=convo_id)
        payload = {
                "model": self.engine,
                "messages": self.conversation[convo_id]['history'],
                "stream": False,
                # kwargs
                "temperature": kwargs.get("temperature", self.temperature),
                "top_p": kwargs.get("top_p", self.top_p),
                "presence_penalty": kwargs.get(
                    "presence_penalty",
                    self.presence_penalty,
                ),
                "frequency_penalty": kwargs.get(
                    "frequency_penalty",
                    self.frequency_penalty,
                ),
                "n": kwargs.get("n", self.reply_count),
                "user": role,
                "max_tokens": self.get_max_tokens(convo_id=convo_id),
            }
        # Get response
        try_index = 0
        response: aiohttp.ClientResponse
        while try_index < 3:
            try:
                async with aiohttp.ClientSession() as ss:
                    log.debug(f"Request payload: {payload}")
                    response = await ss.post(
                        os.environ.get("API_URL") or "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {kwargs.get('api_key', self.api_key)}"},
                        json= payload,
                        ssl = False,
                        proxy = self.proxy
                    )
                break
            except requests.exceptions.ProxyError as e:
                log.exception(e)
                log.info(f"Proxy: {self.proxy}")
            finally:
                try_index += 1
                if try_index == 3:
                    return msg_id, f"Error: {e}"

        match response.status:
            case 401:
                raise Exception(f"Error: {response.status} {response.reason} {await response.text()}\n API_KEY: {kwargs.get('api_key', self.api_key)}")
            case 200:
                pass
            case _:
               raise Exception(
                f"Error: {response.status} {response.reason} {await response.text()}",
            ) 
            

        # log.debug(f"{response.text=}")
        # async for line, _ in response.content.iter_chunks():
        resp = await response.json()
        # TODO save usage info
        usage: dict = resp['usage']
        choices: dict = resp['choices'][0] # type: ignore
        if not choices:
            log.error(f"Error in response: {resp}")
            return msg_id, "Error"
        response_role = choices['message']['role']
        full_response = choices['message']['content'].strip()
        self.calculate_token(convo_id=convo_id, usage= usage)

        if self.conversation[convo_id]['use_history']:
            self.add_to_conversation(full_response, response_role, convo_id=convo_id)
        return msg_id, full_response

    def rollback(self, n: int = 1, convo_id: str = "default") -> None:
        """
        Rollback the conversation
        """
        for _ in range(n):
            self.conversation[convo_id]['history'].pop()

    def reset(self, convo_id: str = "default", system_prompt: str = '') -> None:
        """
        Reset the conversation
        """
        if self.conversation.get(convo_id):
            self.conversation[convo_id]['history'] = [
                {"role": "system", "content": system_prompt or self.system_prompt},
            ]
        else:
            self.new_user(convo_id)

    def new_user(self, convo_id: str = 'default', system_prompt: str = "") -> dict:
        """
        Open new session for new user
        """
        log.debug(f"Creating new user {convo_id}, {system_prompt}")
        self.conversation[convo_id] = {
            'history': [{'role': 'system', 'content': system_prompt or self.system_prompt}],
            'use_history': False,
            'token_tt': 0,
            'token_ask': 0,
            'token_anwser': 0
        }
        return self.conversation

    def calculate_token(self, convo_id: str, usage: dict) -> None:
        """Calculate token costs, only for stream = False

        Args:
            convo_id (str): sender address
            usage (dict): {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
        """
        self.conversation[convo_id]['token_ask'] += usage['prompt_tokens']
        self.conversation[convo_id]['token_anwser'] += usage['completion_tokens']
        self.conversation[convo_id]['token_tt'] += usage['total_tokens']
    
    def token_usage(self, convo_id: str) -> str:
        return f"{self.conversation[convo_id]['token_tt']}"

    def save(self, file: str, *keys: str) -> None:
        """
        Save the Chatbot configuration to a JSON file
        """
        all_obj = {
            key: self.__dict__[key]
            for key in get_filtered_keys_from_object(self, *keys)
        }
        # if 'session' in all_obj:
        #     all_obj['session'] = all_obj['session'].proxies
        # log.debug(f"{json.dumps(all_obj, default=lambda o: str(o))=}")
        with open(file, "w", encoding="utf-8") as f:
            json.dump(
                all_obj,
                f,
                indent=2,
                # saves session.proxies dict as session
                # default=lambda o: o.__dict__["proxies"],
            )

    def load(self, file: str, *_keys: str) -> None:
        """
        Load the Chatbot configuration from a JSON file
        """
        if not pathlib.Path(file).exists():
            return 
        
        with open(file, encoding="utf-8") as f:
            # load json, if session is in keys, load proxies
            loaded_config = json.load(f)
            keys = get_filtered_keys_from_object(self, *_keys)
            log.debug(f"Filtered keys: {keys}")

            # if "session" in keys and loaded_config["session"]:
            #     self.session.proxies = loaded_config["session"]
            # keys = keys - {"session"}
            self.__dict__.update({key: loaded_config[key] for key in keys if key in loaded_config})

    def load_test(self, *keys) -> None:
        """
        test
        """
        # r = get_filtered_keys_from_object(self, *keys)
        log.debug(self.conversation['default']['history'])

    def __del__(self) -> None:
        self.save(CFG.C['ChatGPT']['CONF_FP'])

    async def __aexit__(self) -> None:
        print("aexit")


async def main():
    chat_ = Chatbot(
        api_key='',
        stream=False
    )
    chat_.load_test()
    # chat_.conversation['default'].use_history = True
    # a_gen = chat_.aask_stream("你好，我叫刘培强")
    # print(type(a_gen), a_gen)
    # async for _s in a_gen:
    #     sys.stdout.write(_s)
    #     print()
    # # log.debug(f"{res=}")
    # a_gen = chat_.aask_stream("你好，我叫什么名字？")
    # # log.debug(f"{res=}")
    # async for _s in a_gen:
    #     sys.stdout.write(_s)
    #     print()
    question = {
        '1': '你好，我叫刘培强',
        '2': 'Linux系统发行版有哪些？'
    }

    tasks = []
    for msg_id, prompt in question.items():
        tasks.append(asyncio.create_task(chat_.aask(prompt=prompt, msg_id=msg_id)))
    res = await asyncio.gather(*tasks)
    for msg_id, cont in res:
        print(f"Q: {question[msg_id]}\nA: {cont}")
        print()


if __name__ == '__main__':
    asyncio.run(main())
