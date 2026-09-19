import time

import numpy as np
import sounddevice as sd


class AudioSource:
    def __init__(
        self,
        threshold=0.04,
        cooldown=0.25,
        samplerate=44100,
        blocksize=1024,
        candidate_id=1
    ):
        # threshold 是音量阈值。
        # 声音音量超过这个值时，认为可能发生了一次敲击。
        self.threshold = threshold

        # cooldown 是冷却时间。
        # 一次触发之后，短时间内不要重复触发。
        self.cooldown = cooldown

        # 麦克风采样参数。
        self.samplerate = samplerate
        self.blocksize = blocksize

        # 声音输入暂时只对应食指。
        # candidate_id = 1 表示这次输入由 1 号手指触发。
        self.candidate_id = candidate_id

        # 当前音量，用来显示和调试。
        self.current_rms = 0.0

        # 上一次触发的时间，用来做 cooldown。
        self.last_trigger_time = 0.0

        # 等待主程序读取的 candidate。
        # -1 表示当前没有新的输入触发。
        self.pending_candidate = -1

        # 创建麦克风输入流。
        # audio_callback 会在后台不断收到声音数据。
        self.stream = sd.InputStream(
            channels=1,
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            callback=self.audio_callback
        )

    def audio_callback(self, indata, frames, time_info, status):
        # 如果麦克风流有异常状态，打印出来方便调试。
        if status:
            print(status)

        # indata 是这一小段声音数据。
        # channels=1，所以这里只取第 0 个声道。
        audio = indata[:, 0]

        # RMS 可以理解成这一小段声音的音量大小。
        rms = np.sqrt(np.mean(audio * audio))
        self.current_rms = rms

        now = time.time()

        # 如果音量超过阈值，并且距离上一次触发已经过了 cooldown，
        # 就记录一次新的 candidate。
        if rms > self.threshold:
            if now - self.last_trigger_time > self.cooldown:
                self.pending_candidate = self.candidate_id
                self.last_trigger_time = now

    def start(self):
        # 开始监听麦克风。
        self.stream.start()

    def stop(self):
        # 停止并关闭麦克风输入流。
        self.stream.stop()
        self.stream.close()

    def get_candidate(self):
        # 主程序每一帧会调用这个函数读取 candidate。
        # 读完后立刻重置成 -1，避免一次声音被重复使用。
        candidate = self.pending_candidate
        self.pending_candidate = -1
        return candidate

    def get_volume(self):
        # 返回当前音量，方便显示和调参。
        return self.current_rms