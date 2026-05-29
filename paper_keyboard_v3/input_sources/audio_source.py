import time

import numpy as np
import sounddevice as sd


class AudioSource:
    """
    麦克风敲击检测输入源。

    当前版本只做一件事：
    当麦克风音量突然超过阈值时，认为发生了一次敲击。

    它不负责：
    1. 判断手指在哪个键上
    2. 判断哪个手指是 candidate
    3. 保存输入文本

    它只提供：
    get_tap() -> 是否刚刚检测到一次敲击
    """

    def __init__(
        self,
        threshold=0.04,
        cooldown=0.25,
        samplerate=44100,
        blocksize=1024,
        device=None
    ):
        self.threshold = threshold
        self.cooldown = cooldown
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
        我们用 RMS 计算这一小段声音的整体音量。
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

    def get_volume(self):
        """返回当前麦克风音量。"""
        return self.current_volume


def main():
    audio_source = AudioSource(
        threshold=0.04,
        cooldown=0.25
    )

    audio_source.start()

    print("AudioSource 敲击检测测试开始")
    print("敲一下桌面或纸面，如果检测到，会输出 TAP")
    print("如果太敏感，就调高 threshold")
    print("如果检测不到，就调低 threshold")
    print("按 Ctrl+C 退出")

    try:
        while True:
            volume = audio_source.get_volume()

            if audio_source.get_tap():
                print(f"TAP! volume={volume:.4f}")
            else:
                print(f"volume={volume:.4f}", end="\r")

            time.sleep(0.03)

    except KeyboardInterrupt:
        pass

    audio_source.stop()
    print()
    print("AudioSource 敲击检测测试结束")


if __name__ == "__main__":
    main()