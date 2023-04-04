import argparse
import typing
import logging

log = logging.getLogger('app.args')

def get_args(args_: typing.List) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api_key", type=str, help="OpenAI API key")
    parser.add_argument("--bot", type=str, choices=['chatgpt'], default='chatgpt', help="Chatbot name")
    # parser.add_argument("--imsg", action="store_true", help="Use for imsg or server listening")
    parser.add_argument("--execute", type=str, choices=["imsg", "wecomserver", "wecomsrv_callback", "webserver"], help="xxx")
    parser.add_argument("--stream", action="store_true", help="Enable streaming")
    parser.add_argument("--temperature", type=float, default=0.6, help="Temperature for response")
    parser.add_argument("--proxy", type=str, default=None, help="Proxy address")
    parser.add_argument("--use_history", action="store_true", required='--multi_people' in args_, help = "Single-turn or multi-turn chat")
    parser.add_argument("--multi_people", action="store_true", help="New conversation id for everyone people")
    args = parser.parse_args(args_)
    log.debug(f"{args=}")
    return args


