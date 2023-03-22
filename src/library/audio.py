# -*- encoding: utf-8 -*-
'''
@File    :   record.py
@Time    :   2023/03/17 09:56:36
@Author  :   Yohann Li
@Version :   1.0
@Contact :   intelligenct@gmail.com
@Desc    :   records voice
'''

# here put the import lib
import logging
import sys
import time
from typing import Text, Dict, List, Generator, ByteString, Union, BinaryIO
import pathlib
import wave
import io

import pyaudio

logger = logging.getLogger('app.audio')


class Audio:
    """
    record or play audio w/ pyaudio
    """

    def __init__(
            self, 
            format: int = pyaudio.paInt16,
            channels: int = 1,
            rate: int = 16000,
            chunk_size: int = 5120
        ):
        self.p = pyaudio.PyAudio()
        self.r_format = format
        self.r_channel = channels
        self.r_rate = rate
        self.r_chunk = chunk_size
        # self.r_interval = 0.1

    def get_record_stream(self) -> pyaudio.PyAudio.Stream:
        stream = self.p.open(
            rate = self.r_rate,
            channels = self.r_channel,
            format= self.r_format,
            input= True,
            frames_per_buffer = self.r_chunk,
        )
        return stream

    def record_stream(self, duration: int) -> Generator:
        """
        录音并流式输出
        """
        stream = self.get_record_stream()
        if duration > 0:
            logger.info(f"Recording for {duration} seconds")
            for _ in range(int(self.r_rate * duration / self.r_chunk)):
                sys.stdout.write(f"\rrecording {_}")
                yield stream.read(self.r_chunk)
            logger.debug(f"Record finished")
            stream.stop_stream()
            stream.close()

    def record(self, duration: int = 10) -> ByteString:
        """
        录音
        """
        data = b""
        _gen = self.record_stream(duration)
        try:
            while True:
                part = next(_gen)
                data += part
        except StopIteration as e:
            logger.exception(e)
            pass

        return data

    def record_to_wav(self, fp: Text, duration: int = 30) -> int:
        """
        录音并保存到文件，格式: wav
        """
        data = self.record(duration)
        return self.save_wav(data, fp)

    def play_stream(self, file_object: Union[Text, BinaryIO, wave.Wave_read]) -> Generator:
        """
        流式读取文件并返回生成器
        """
        if isinstance(file_object, Text):
            with open(file_object) as wf:
                return self.play_stream(wf)
        while data := file_object.readframes(self.r_chunk):
            yield data

    def play(self, fp: Text) -> ByteString:
        """
        读取并播放 wav 音频文件
        """
        with wave.open(fp, 'rb') as wf:
            stream = self.p.open(
                format=self.p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate = wf.getframerate(),
                output=True,
            )
            for data in self.play_stream(wf):
                stream.write(data)

    def save_wav(self, data: ByteString, fp: Text) -> int:
        logger.info(f'Saving wav format file: {fp}')
        with wave.open(fp, 'wb') as wf:
            wf.setnchannels(self.r_channel)
            wf.setsampwidth(self.p.get_sample_size(self.r_format))
            wf.setframerate(self.r_rate)
            wf.writeframes(data)

        return 0

    def release_audio(self) -> int:
        self.p.terminate()
        return 0
    
    def __del__(self):
        try:
            self.release_audio()
        except Exception as e:
            logger.warning("释放audio资源时出错，已忽略")
            logger.exception(e)


def wav2pcm(wav_fp: Text, pcm_fp: Text):
    pass



def main():
    wav_fp = "D:\\projects\\ChatGPT-iMessage\\audio\\first_audio.wav"
    aud = Audio()
    aud.record_to_wav(wav_fp)
    time.sleep(1)
    logger.info("开始播放录音")
    aud.play_stream(wav_fp)
    return 0


if __name__ == '__main__':
    logging.basicConfig(
        datefmt='%F %T',
        format= "%(asctime)s %(name)s %(funcName)s %(lineno)s %(levelname)s | %(message)s",
        level = logging.DEBUG)
    main()