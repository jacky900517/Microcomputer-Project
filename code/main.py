try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from code.config import GAME_LOOP_MS, INPUT_POLL_MS
from code.display_unit import DisplayUnit
from code.game import GameEngine
from code.input_unit import InputUnit
from code.joystick import Joystick
from code.score_manager import ScoreManager
from code.sounds import SoundManager


async def sleep_ms(duration_ms):
    # 包裝 sleep，讓 MicroPython 和電腦端測試都能用同一個非阻塞等待寫法。
    if hasattr(asyncio, "sleep_ms"):
        await asyncio.sleep_ms(duration_ms)
    else:
        await asyncio.sleep(duration_ms / 1000)


async def input_task(input_unit, joystick):
    # 獨立掃描輸入，避免主遊戲迴圈太忙時漏掉按鈕或搖桿事件。
    while True:
        input_unit.poll_buttons()
        direction = joystick.direction()
        if direction is not None:
            input_unit.push_event(direction)
        await sleep_ms(INPUT_POLL_MS)


async def sound_task(game, sound_manager):
    # 音效獨立播放，先處理按鍵/過關音效，沒有事件時才播放倒數背景音。
    while True:
        snapshot = game.get_snapshot()
        sound_manager.set_volume(snapshot.get("volume", 60))
        effect_name = game.pop_sound_event()
        if effect_name is not None:
            await sound_manager.play_effect(effect_name)
        else:
            await sound_manager.play_bgm(snapshot.get("bgm_phase", "silent"))


async def game_loop(game, display, input_unit, score_manager):
    # 主遊戲迴圈負責 FSM、分數儲存與畫面更新，是整個遊戲的主要流程。
    while True:
        events = input_unit.read_events()
        game.update(events)

        score_to_save = game.consume_score_to_save()
        if score_to_save is not None:
            records = score_manager.save_score(score_to_save)
            game.set_score_records(records)

        display.render(game.get_snapshot())
        await sleep_ms(GAME_LOOP_MS)


async def main():
    # 建立所有模組物件並啟動 uasyncio 任務，讓 main.py 保持簡短。
    game = GameEngine()
    display = DisplayUnit()
    input_unit = InputUnit()
    joystick = Joystick()
    score_manager = ScoreManager()
    sound_manager = SoundManager()

    game.set_score_records(score_manager.load_scores())
    asyncio.create_task(input_task(input_unit, joystick))
    asyncio.create_task(sound_task(game, sound_manager))
    await game_loop(game, display, input_unit, score_manager)


try:
    asyncio.run(main())
finally:
    # 程式停止後重設 asyncio 狀態，避免在 MicroPython 互動環境重跑時卡住。
    if hasattr(asyncio, "new_event_loop"):
        asyncio.new_event_loop()
