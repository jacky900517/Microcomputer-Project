import time

from code.config import (
    EVENT_DOWN,
    EVENT_LEFT,
    EVENT_RIGHT,
    EVENT_UP,
    JOYSTICK_REPEAT_MS,
    PIN_JOYSTICK_X,
    PIN_JOYSTICK_Y,
)


def ticks_ms():
    # 取得毫秒時間，電腦端沒有 time.ticks_ms() 時改用 time.time() 模擬。
    try:
        return time.ticks_ms()
    except AttributeError:
        return int(time.time() * 1000)


def ticks_diff(now_ms, before_ms):
    # 計算兩個毫秒時間差，保留 MicroPython ticks 迴繞時也安全的寫法。
    try:
        return time.ticks_diff(now_ms, before_ms)
    except AttributeError:
        return now_ms - before_ms


class Joystick:
    def __init__(self, x_pin=PIN_JOYSTICK_X, y_pin=PIN_JOYSTICK_Y):
        # 初始化搖桿 ADC 腳位，若在沒有 Pico 的環境執行就進入無硬體模式。
        self.hardware = False
        self.x_adc = None
        self.y_adc = None
        self.low_threshold = 22000
        self.high_threshold = 43000
        self.last_direction = None
        self.last_direction_ms = 0

        try:
            from machine import ADC, Pin

            self.x_adc = ADC(Pin(x_pin))
            self.y_adc = ADC(Pin(y_pin))
            self.hardware = True
        except Exception:
            self.hardware = False

    def direction(self):
        # 將 VRx/VRy 類比值轉成上下左右事件，讓 game.py 不需要知道 ADC 細節。
        if not self.hardware:
            return None

        x_value = self.x_adc.read_u16()
        y_value = self.y_adc.read_u16()
        direction = None

        if x_value < self.low_threshold:
            direction = EVENT_DOWN
        elif x_value > self.high_threshold:
            direction = EVENT_UP
        elif y_value < self.low_threshold:
            direction = EVENT_LEFT
        elif y_value > self.high_threshold:
            direction = EVENT_RIGHT

        return self._repeat_limited(direction)

    def volume_level(self):
        # 將 VRy 類比值換算成 0 到 100 的音量值，保留給音量設定使用。
        if not self.hardware:
            return 60

        raw_value = self.y_adc.read_u16()
        volume = int(raw_value * 100 // 65535)
        return self._clamp(volume, 0, 100)

    def _repeat_limited(self, direction):
        # 限制長推搖桿的重複觸發速度，避免玩家一次滑動就連走太多格。
        now_ms = ticks_ms()
        if direction is None:
            self.last_direction = None
            return None

        if direction != self.last_direction:
            self.last_direction = direction
            self.last_direction_ms = now_ms
            return direction

        if ticks_diff(now_ms, self.last_direction_ms) >= JOYSTICK_REPEAT_MS:
            self.last_direction_ms = now_ms
            return direction

        return None

    def _clamp(self, value, low, high):
        # 將數值限制在指定範圍內，避免音量或其他數值超出合理上下限。
        if value < low:
            return low
        if value > high:
            return high
        return value
