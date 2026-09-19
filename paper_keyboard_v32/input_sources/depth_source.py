import time


class DepthSource:
    """
    使用 MediaPipe landmark.z 做一个很粗糙的“按下”实验。

    这个类的接口故意做得和 AudioSource 类似：
        start()
        stop()
        get_candidate()

    另外多了一个 update(hand_data)，由 FrameBuilder 每一帧把 MediaPipe 的手部数据传进来。

    当前实验规则：
        程序启动后，先收集一小段食指 z 作为 baseline。
        后面如果食指 z 比 baseline 大一段，就认为食指向纸面按下了。

    注意：
        MediaPipe 的 z 不是准确的真实深度，只适合做快速实验。
        如果发现“抬手触发、按下不触发”，可以把 direction 改成 "decrease"。
    """

    def __init__(
        self,
        candidate_id=1,
        finger_id=1,
        press_delta=0.025,
        cooldown=0.35,
        baseline_count=30,
        direction="increase"
    ):
        self.candidate_id = candidate_id
        self.finger_id = finger_id
        self.press_delta = press_delta
        self.cooldown = cooldown
        self.baseline_count = baseline_count
        self.direction = direction

        self.baseline_values = []
        self.baseline_z = None

        self.current_z = None
        self.is_pressed = False
        self.last_pressed = False
        self.tap_detected = False
        self.last_tap_time = 0.0

    def start(self):
        """为了兼容原来的 main.py，保留 start()，但这里不需要真的启动什么。"""
        print("DepthSource 深度按下实验开始")
        print("启动后先让右手食指保持在纸面上方/正常悬停一小会儿，用来校准 baseline")
        print("如果方向反了，可以把 programs/main.py 里的 direction 改成 decrease")

    def stop(self):
        """为了兼容原来的 main.py，保留 stop()。"""
        pass

    def find_fingertip(self, hand_data):
        """从 hand_data 里找到指定 finger_id 的指尖。"""
        for fingertip in hand_data["fingertips"]:
            if fingertip["finger_id"] == self.finger_id:
                return fingertip

        return None

    def update_baseline(self, z):
        """收集一小段 z，作为没有按下时的大致 baseline。"""
        if self.baseline_z is not None:
            return

        self.baseline_values.append(z)

        if len(self.baseline_values) >= self.baseline_count:
            self.baseline_z = sum(self.baseline_values) / len(self.baseline_values)
            print()
            print("DepthSource baseline_z =", round(self.baseline_z, 4))
            print("press_delta =", self.press_delta)
            print("direction =", self.direction)
            print("现在可以尝试用右手食指按纸面键盘。")
            print()

    def check_pressed(self, z):
        """根据当前 z 和 baseline 判断是否按下。"""
        if self.baseline_z is None:
            return False

        if self.direction == "increase":
            return z > self.baseline_z + self.press_delta

        if self.direction == "decrease":
            return z < self.baseline_z - self.press_delta

        return False

    def update(self, hand_data):
        """
        每一帧调用一次。

        hand_data 来自 MediaPipeHandSource.process_image(image)。
        """
        fingertip = self.find_fingertip(hand_data)

        if fingertip is None:
            self.current_z = None
            self.is_pressed = False
            self.last_pressed = False
            return

        if "z" not in fingertip:
            self.current_z = None
            self.is_pressed = False
            self.last_pressed = False
            return

        z = fingertip["z"]
        self.current_z = z

        self.update_baseline(z)

        pressed = self.check_pressed(z)
        now = time.time()

        is_new_press = (
            pressed
            and not self.last_pressed
            and now - self.last_tap_time > self.cooldown
        )

        if is_new_press:
            self.tap_detected = True
            self.last_tap_time = now
            print("Depth tap:", "z=", round(z, 4), "baseline=", round(self.baseline_z, 4))

        self.is_pressed = pressed
        self.last_pressed = pressed

    def get_candidate(self):
        """
        返回当前输入触发手指。

        没有检测到按下：-1
        检测到一次新的按下：candidate_id
        """
        if self.tap_detected:
            self.tap_detected = False
            return self.candidate_id

        return -1

    def get_depth_info(self):
        """给调试用。"""
        return {
            "current_z": self.current_z,
            "baseline_z": self.baseline_z,
            "is_pressed": self.is_pressed,
            "press_delta": self.press_delta,
            "direction": self.direction
        }


if __name__ == "__main__":
    print("DepthSource 需要从 app.py 的主程序里配合摄像头和 MediaPipe 使用。")
