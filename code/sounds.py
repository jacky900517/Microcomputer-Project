try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from code.config import PIN_BUZZER, SOUND_KEY, SOUND_LEVEL_CLEAR, SOUND_LOSE, SOUND_WIN


async def sleep_ms(duration_ms):
    # 包裝非阻塞等待，讓音符播放時不會卡住輸入和畫面任務。
    if hasattr(asyncio, "sleep_ms"):
        await asyncio.sleep_ms(duration_ms)
    else:
        await asyncio.sleep(duration_ms / 1000)


class SoundManager:
    def __init__(self, buzzer_pin=PIN_BUZZER):
        # 初始化蜂鳴器 PWM，並準備背景音樂與事件音效的音符表。
        self.hardware = False
        self.pwm = None
        self.volume = 60
        self.current_phase = None
        self.phase_index = 0

        try:
            from machine import PWM, Pin

            self.pwm = PWM(Pin(buzzer_pin, Pin.OUT))
            self.hardware = True
            self.stop()
        except Exception:
            self.hardware = False

        self.bgm_patterns = {
            "normal": ((523, 160), (659, 160), (784, 160), (659, 160)),
            "tension": ((659, 110), (784, 110), (988, 110), (784, 110)),
            "urgent": ((1047, 70), (0, 70), (1047, 70), (0, 70)),
        }
        self.effect_patterns = {
            SOUND_KEY: ((523, 60),),
            SOUND_LEVEL_CLEAR: ((784, 120), (1047, 120), (1319, 120)),
            SOUND_WIN: ((523, 180), (659, 180), (784, 180), (1047, 180), (784, 180), (1047, 180)),
            SOUND_LOSE: ((659, 220), (523, 220), (440, 220), (349, 220)),
        }

    def set_volume(self, volume):
        # 設定 0 到 100 的音量百分比，播放音符時再轉成 PWM duty。
        if volume < 0:
            volume = 0
        if volume > 100:
            volume = 100
        self.volume = int(volume)

    async def play_bgm(self, phase):
        # 播放目前 BGM 階段的一個音，分段播放才能讓其他任務繼續執行。
        if phase not in self.bgm_patterns:
            self.current_phase = None
            self.phase_index = 0
            self.stop()
            await sleep_ms(50)
            return

        if phase != self.current_phase:
            self.current_phase = phase
            self.phase_index = 0

        pattern = self.bgm_patterns[phase]
        frequency, duration_ms = pattern[self.phase_index]
        self.phase_index = (self.phase_index + 1) % len(pattern)
        await self._play_note(frequency, duration_ms)
        self.stop()
        await sleep_ms(30)

    async def play_effect(self, effect_name):
        # 播放短音效，例如按鍵、過關、成功或失敗，優先於背景音樂。
        pattern = self.effect_patterns.get(effect_name, ())
        for frequency, duration_ms in pattern:
            await self._play_note(frequency, duration_ms)
            self.stop()
            await sleep_ms(35)

    def stop(self):
        # 立即關閉 PWM duty，讓蜂鳴器停止發聲。
        if self.hardware and self.pwm is not None:
            self.pwm.duty_u16(0)

    def deinit(self):
        # 釋放 PWM 資源，程式結束或除錯時可避免蜂鳴器持續發聲。
        if self.hardware and self.pwm is not None:
            self.stop()
            self.pwm.deinit()

    async def _play_note(self, frequency, duration_ms):
        # 播放單一音符；frequency 為 0 或音量為 0 時視為休止。
        if not self.hardware or frequency <= 0 or self.volume <= 0:
            self.stop()
            await sleep_ms(duration_ms)
            return

        self.pwm.freq(int(frequency))
        self.pwm.duty_u16(self._volume_duty())
        await sleep_ms(duration_ms)

    def _volume_duty(self):
        # 用平方曲線轉換音量，讓低音量與高音量的聽感差異更明顯。
        return int((self.volume * self.volume * 32768) // 10000)
