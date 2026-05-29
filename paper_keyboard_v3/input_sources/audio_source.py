import time

import numpy as np
import sounddevice as sd


class AudioSource:
    """
    麦克风敲击检测输入源。

    当前版本用于基础版纸面键盘：

    没有检测到敲击：
        get_candidate() 返回 -1

    检测到敲击：
        get_candidate() 返回 candidate_id

    当前 candidate_id 默认为 1，也就是右手食指。
    以后如果换成指套、手套或串口按钮输入源，
    新的 source 可以直接返回 -1 到 9。
    """

    def __init__(
        self,
        threshold=0.04,
        cooldown=0.25,
        candidate_id=1,
        samplerate=44100,
        blocksize=1024,
        device=None
    ):
        self.threshold = threshold
        self.cooldown = cooldown
        self.candidate_id = candidate_id

        self.samplerate = samplerate
        self.blocksize = blocksize
        self.device = device

        self.current_volume = 0.0
        self.tap_detected = False
        self.last_tap_time = 0.0

        self.stream = None

    def audio_callback(self, indata, frames, time_info, status):
        """
        sounddevice 会自动反复调用这个函数。

        indata 是当前这一小段麦克风数据。
        这里用 RMS 计算这一小段声音的整体音量。
        """
        if status:
            print(status)

        volume = np.sqrt(np.mean(indata ** 2))
        self.current_volume = float(volume)

        now = time.time()

        is_loud = self.current_volume > self.threshold
        is_after_cooldown = now - self.last_tap_time > self.cooldown

        if is_loud and is_after_cooldown:
            self.tap_detected = True
            self.last_tap_time = now

    def start(self):
        """开始监听麦克风。"""
        self.stream = sd.InputStream(
            device=self.device,
            channels=1,
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            callback=self.audio_callback
        )

        self.stream.start()

    def stop(self):
        """停止监听麦克风。"""
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def get_tap(self):
        """
        返回是否检测到一次新的敲击。

        注意：
        一旦返回 True，就会立刻清空状态。
        所以同一次敲击只会被读取一次。
        """
        if self.tap_detected:
            self.tap_detected = False
            return True

        return False

    def get_candidate(self):
        """
        返回当前输入候选手指。

        当前音频基础版：
            没有敲击 -> -1
            检测到敲击 -> candidate_id

        默认 candidate_id = 1，表示右手食指。
        """
        if self.get_tap():
            return self.candidate_id

        return -1

    def get_volume(self):
        """返回当前麦克风音量。"""
        return self.current_volume


def main():
    audio_source = AudioSource(
        threshold=0.04,
        cooldown=0.25,
        candidate_id=1
    )

    audio_source.start()

    print("AudioSource 敲击检测测试开始")
    print("检测到敲击时，candidate 应该输出 1")
    print("没有敲击时，candidate 输出 -1")
    print("如果太敏感，就调高 threshold")
    print("如果检测不到，就调低 threshold")
    print("按 Ctrl+C 退出")

    try:
        while True:
            volume = audio_source.get_volume()
            candidate = audio_source.get_candidate()

            if candidate != -1:
                print(f"candidate={candidate}, volume={volume:.4f}")
            else:
                print(f"candidate={candidate}, volume={volume:.4f}", end="\r")

            time.sleep(0.03)

    except KeyboardInterrupt:
        pass

    audio_source.stop()
    print()
    print("AudioSource 敲击检测测试结束")


if __name__ == "__main__":
    main()