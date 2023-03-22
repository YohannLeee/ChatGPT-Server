from AIGC.ChatGPT import Chatbot


def get_chat_bot(name):
    match name.lower():
        case 'chatgpt':
            return Chatbot
        case _:
            raise ModuleNotFoundError(name=name)