# -*- encoding: utf-8 -*-
'''
@File    :   test_wave_read.py
@Time    :   2023/03/28 22:35:57
@Author  :   Yohann Li
@Version :   1.0
@Contact :   intelligenct@gmail.com
@Desc    :   None
'''

# here put the import lib
import wave






def wav_file_stream(fp: str, chunk_size: int = 1024):
    with wave.open(fp, "rb") as wf:
        # while data := wf.readframes(chunk_size):
        #     yield data
        pass




def main():
    wav_fp = "/home/yohann/.AIGCSrv/media/voice/20230328_222230.wav"
    wav_file_stream(fp=wav_fp)
    return 0


if __name__ == '__main__':
    main()