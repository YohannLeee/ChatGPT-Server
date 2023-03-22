# -*- encoding: utf-8 -*-
'''
@File    :   windows_api.py
@Time    :   2023/03/18 12:03:26
@Author  :   Yohann Li
@Version :   1.0
@Contact :   intelligenct@gmail.com
@Desc    :   convert text to 
'''

# here put the import lib
import queue
import threading
import logging
import pathlib
import sys

sys.path.append(pathlib.Path(__file__).parent.parent.as_posix())

import win32com.client
import pyttsx3


from settings import conf

logger = logging.getLogger('app.winapi')






def test_pyttsx3():
    import pyttsx3
    from datetime import datetime as dt
    engine = pyttsx3.init() # object creation

    """ RATE"""
    rate = engine.getProperty('rate')   # getting details of current speaking rate
    print (rate)                        #printing current voice rate
    engine.setProperty('rate', 200)     # setting up new voice rate


    """VOLUME"""
    volume = engine.getProperty('volume')   #getting to know current volume level (min=0 and max=1)
    print (volume)                          #printing current volume level
    engine.setProperty('volume',1.0)    # setting up volume level  between 0 and 1

    """VOICE"""
    voices = engine.getProperty('voices')       #getting details of current voice
    engine.setProperty('voice', voices[0].id)  #changing index, changes voices. o for male
    # engine.setProperty('voice', voices[1].id)   #changing index, changes voices. 1 for female

    engine.say(f"你好，现在是晚")
    engine.say(f"上{dt.strftime(dt.now(), '%H:%M')}")
    engine.runAndWait()
    engine.stop()

    """Saving Voice to a file"""
    # On linux make sure that 'espeak' and 'ffmpeg' are installed
    # engine.save_to_file('Hello World', 'test.mp3')
    engine.runAndWait()


def test_pyttsx3_in_thread():
    import pyttsx3
    from datetime import datetime as dt
    engine = pyttsx3.init() # object creation
    text_que = queue.Queue()

    """ RATE"""
    rate = engine.getProperty('rate')   # getting details of current speaking rate
    print (rate)                        #printing current voice rate
    engine.setProperty('rate', 200)     # setting up new voice rate


    """VOLUME"""
    volume = engine.getProperty('volume')   #getting to know current volume level (min=0 and max=1)
    print (volume)                          #printing current volume level
    engine.setProperty('volume',1.0)    # setting up volume level  between 0 and 1

    """VOICE"""
    voices = engine.getProperty('voices')       #getting details of current voice
    engine.setProperty('voice', voices[0].id)  #changing index, changes voices. o for male
    # engine.setProperty('voice', voices[1].id)   #changing index, changes voices. 1 for female
    def say_in_thread():
        logger.debug("Start thread")
        while True:
            logger.debug("Looping")
            text = text_que.get()
            if text is None:
                logger.debug("Break while loop")
                break
            logger.debug(f"{text=}")
            engine.say(text)
        logger.debug(f"{engine.proxy._queue=}")
        engine.runAndWait()
        engine.stop()
        logger.debug("Exiting thread")

    """Saving Voice to a file"""
    # On linux make sure that 'espeak' and 'ffmpeg' are installed
    # engine.save_to_file('Hello World', 'test.mp3')
    # engine.runAndWait()

    th = threading.Thread(target=say_in_thread)
    th.start()
    text_que.put("你好，现在是晚")
    text_que.put(f"上{dt.strftime(dt.now(), '%H:%M')}")
    text_que.put(None)
    th.join()


def test_pytss_gpt():
    # # 创建一个线程安全的队列
    # text_queue = queue.Queue()

    # # 创建一个 pyttsx3 引擎实例
    # engine = pyttsx3.init()

    # # 定义一个播放语音的函数
    # def play_voice():
    #     while True:
    #         # 从队列中获取待播放的文本
    #         text = text_queue.get()
    #         if text is None:
    #             text_queue.task_done()  # 标记已处理完毕
    #             break
    #         # 将文本转换为语音并播放
    #         engine.say(text)
    #         engine.runAndWait()
    #         engine.
    #         text_queue.task_done()  # 标记已处理完毕

    # # 创建一个线程来播放语音
    # voice_thread = threading.Thread(target=play_voice)
    # voice_thread.start()

    # # 在主线程中向队列中添加待播放的文本
    # text_queue.put("Hello, World!")
    # text_queue.put("How are you?")
    # text_queue.put(None)  # 发送一个 None，表示队列已结束

    # # 等待语音播放线程结束
    # text_queue.join()
    # voice_thread.join()


    engine = pyttsx3.init()

    engine.addText("Hello")
    engine.addText("How are you?")
    engine.runAndWait()




def test_w32_speak():
    spk = win32com.client.Dispatch("SAPI.SpVoice")
    def run_in_thread():
        spk.Speak("你好，现在是中")
        spk.Speak("午12:07")
    th = threading.Thread(target=run_in_thread)
    th.start()
    th.join()


def main():
    logger.debug("Enter main function")
    test_pyttsx3_in_thread()
    # test_pyttsx3()
    # test_w32_speak()
    # test_pytss_gpt()
    logger.debug("Exit main function")
    return 0


if __name__ == '__main__':
    main()