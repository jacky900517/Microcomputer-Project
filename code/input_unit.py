import time

from code.config import (
    BUTTON_DEBOUNCE_MS,
    EVENT_BACK,
    EVENT_CONFIRM,
    PIN_BUTTON_A,
    PIN_BUTTON_B,
    PIN_JOYSTICK_SW,
)


def ticks_ms():
    # 取得毫秒時間，讓按鈕去彈跳可以在 MicroPython 和電腦端共用。
    try:
        return time.ticks_ms()
    except AttributeError:
        return int(time.time() * 1000)


def ticks_diff(now_ms, before_ms):
    # 計算時間差，使用 MicroPython 的 ticks_diff 避免毫秒計數器迴繞問題。
    try:
        return time.ticks_diff(now_ms, before_ms)
    except AttributeError:
        return now_ms - before_ms


class InputUnit:
    def __init__(
        self,
        confirm_pin=PIN_BUTTON_A,
        back_pin=PIN_BUTTON_B,
        joystick_sw_pin=PIN_JOYSTICK_SW,
    ):
        # 建立 A、B、搖桿 SW 的 PULL_UP 輸入，並準備事件佇列給主迴圈讀取。
        self.hardware = False
        self.event_queue = []
        self.buttons = {}
        self.button_down = {}
        self.last_event_ms = {}

        try:
            from machine import Pin

            self.buttons = {
                EVENT_CONFIRM: [
                    Pin(confirm_pin, Pin.IN, Pin.PULL_UP),
                    Pin(joystick_sw_pin, Pin.IN, Pin.PULL_UP),
                ],
                EVENT_BACK: [Pin(back_pin, Pin.IN, Pin.PULL_UP)],
            }
            self.hardware = True
        except Exception:
            self.hardware = False

        for event_name in (EVENT_CONFIRM, EVENT_BACK):
            self.button_down[event_name] = False
            self.last_event_ms[event_name] = 0

    def poll_buttons(self):
        # 每次掃描按鈕一次，只在放開到按下的瞬間產生事件，避免長按連續觸發。
        if not self.hardware:
            return

        now_ms = ticks_ms()
        for event_name, pins in self.buttons.items():
            pressed = self._any_pressed(pins)
            was_down = self.button_down[event_name]
            self.button_down[event_name] = pressed

            if pressed and not was_down:
                elapsed_ms = ticks_diff(now_ms, self.last_event_ms[event_name])
                if elapsed_ms >= BUTTON_DEBOUNCE_MS:
                    self.last_event_ms[event_name] = now_ms
                    self.push_event(event_name)

    def push_event(self, event_name):
        # 將按鈕或搖桿事件放入佇列，讓 GameEngine 一次處理已整理好的事件。
        if event_name is not None:
            self.event_queue.append(event_name)

    def read_events(self):
        # 交出目前累積的事件並清空佇列，避免同一個按鍵被主迴圈重複處理。
        events = self.event_queue
        self.event_queue = []
        return events

    def is_confirm(self, event_name):
        # 判斷事件是否為確認鍵，讓其他模組不用直接比對事件字串。
        return event_name == EVENT_CONFIRM

    def is_back(self, event_name):
        # 判斷事件是否為返回鍵，讓按鍵語意集中在 input_unit.py 裡。
        return event_name == EVENT_BACK

    def _any_pressed(self, pins):
        # PULL_UP 接地按鈕按下時會讀到 0，只要同事件任一腳位按下就回傳 True。
        for button_pin in pins:
            if button_pin.value() == 0:
                return True
        return False
