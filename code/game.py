import time

from code.config import (
    BASE_SCORE,
    DEFAULT_VOLUME,
    EVENT_BACK,
    EVENT_CONFIRM,
    EVENT_DOWN,
    EVENT_LEFT,
    EVENT_RIGHT,
    EVENT_UP,
    LEVEL_STATES,
    LEVEL_TIME_SECONDS,
    PENALTY_PER_SECOND,
    PENALTY_START_SECONDS,
    SOUND_KEY,
    SOUND_LEVEL_CLEAR,
    SOUND_LOSE,
    SOUND_WIN,
    STATE_FINISH,
    STATE_LEVEL_1,
    STATE_LEVEL_2,
    STATE_LEVEL_3,
    STATE_MENU,
    STATE_PAUSE,
    STATE_RANK,
    STATE_SETTING,
)
from code.map_data import END_POINTS, LEVEL_MAPS, START_POINTS


def ticks_ms():
    # 取得目前毫秒時間；在電腦端測試時沒有 ticks_ms() 就改用 time.time()。
    try:
        return time.ticks_ms()
    except AttributeError:
        return int(time.time() * 1000)


def ticks_diff(now_ms, before_ms):
    # 計算經過時間，使用 ticks_diff 是為了處理 MicroPython 計數器迴繞。
    try:
        return time.ticks_diff(now_ms, before_ms)
    except AttributeError:
        return now_ms - before_ms


class GameEngine:
    def __init__(self):
        # 初始化 FSM 狀態、選單游標、玩家位置、分數與計時資料。
        self.state = STATE_MENU
        self.previous_state = STATE_LEVEL_1
        self.menu_items = ("START GAME", "HIGH SCORES", "VOLUME")
        self.pause_items = ("RESUME", "MAIN MENU")
        self.menu_index = 0
        self.pause_index = 0
        self.level_index = 0
        self.player_x = 1
        self.player_y = 1
        self.total_score = 0
        self.final_score = 0
        self.finish_success = False
        self.volume = DEFAULT_VOLUME
        self.level_elapsed_ms = 0
        self.total_elapsed_ms = 0
        self.last_update_ms = ticks_ms()
        self.sound_events = []
        self.needs_score_save = False
        self.score_records = {"top_scores": [], "last_score": 0}

    def update(self, events):
        # 每一幀更新倒計時並處理輸入事件，是 GameEngine 對外的主要更新入口。
        now_ms = ticks_ms()
        elapsed_ms = ticks_diff(now_ms, self.last_update_ms)
        self.last_update_ms = now_ms

        if self.state in LEVEL_STATES:
            self.level_elapsed_ms += max(0, elapsed_ms)
            if self.level_elapsed_ms >= LEVEL_TIME_SECONDS * 1000:
                self._finish_game(False)
                return

        for event_name in events:
            self.handle_input(event_name)

    def handle_input(self, event_name):
        # 依照目前 FSM 狀態分派輸入，避免所有狀態邏輯擠在同一段判斷裡。
        if self.state == STATE_MENU:
            self._handle_menu_input(event_name)
        elif self.state in LEVEL_STATES:
            self._handle_level_input(event_name)
        elif self.state == STATE_PAUSE:
            self._handle_pause_input(event_name)
        elif self.state == STATE_FINISH:
            self._handle_finish_input(event_name)
        elif self.state == STATE_RANK:
            self._handle_rank_input(event_name)
        elif self.state == STATE_SETTING:
            self._handle_setting_input(event_name)

    def get_snapshot(self):
        # 整理目前遊戲資料給顯示與音效模組使用，避免它們直接修改遊戲狀態。
        return {
            "state": self.state,
            "menu_items": self.menu_items,
            "menu_index": self.menu_index,
            "pause_items": self.pause_items,
            "pause_index": self.pause_index,
            "level_number": self.level_index + 1,
            "maze": LEVEL_MAPS[self.level_index],
            "player": (self.player_x, self.player_y),
            "exit": END_POINTS[self.level_index],
            "remaining_seconds": self.remaining_seconds(),
            "total_score": self.total_score,
            "current_score": self.current_level_score(),
            "final_score": self.final_score,
            "finish_success": self.finish_success,
            "elapsed_seconds": self.total_elapsed_ms // 1000,
            "volume": self.volume,
            "bgm_phase": self.bgm_phase(),
            "top_scores": self.score_records.get("top_scores", []),
            "last_score": self.score_records.get("last_score", 0),
        }

    def set_score_records(self, records):
        # 更新 GameEngine 快取的排行榜資料，讓畫面能顯示最新 Flash 紀錄。
        self.score_records = records

    def consume_score_to_save(self):
        # 結算時只交出一次需要儲存的分數，避免主迴圈重複寫入 Flash。
        if not self.needs_score_save:
            return None
        self.needs_score_save = False
        return self.final_score

    def pop_sound_event(self):
        # 取出一個待播放音效事件，讓 sound_task 可以非阻塞地逐一播放。
        if not self.sound_events:
            return None
        return self.sound_events.pop(0)

    def remaining_seconds(self):
        # 依照本關經過時間計算剩餘秒數，提供畫面與扣分邏輯共用。
        if self.state not in LEVEL_STATES and self.state != STATE_PAUSE:
            return LEVEL_TIME_SECONDS
        remaining = LEVEL_TIME_SECONDS - (self.level_elapsed_ms // 1000)
        if remaining < 0:
            return 0
        return remaining

    def current_level_score(self):
        # 根據剩餘秒數計算本關分數，20 秒後開始每秒扣 5 分。
        remaining = self.remaining_seconds()
        penalty_seconds = PENALTY_START_SECONDS - remaining
        if penalty_seconds < 0:
            penalty_seconds = 0
        score = BASE_SCORE - penalty_seconds * PENALTY_PER_SECOND
        if score < 0:
            return 0
        return score

    def bgm_phase(self):
        # 依照倒數時間選擇一般、緊張或急迫 BGM 階段。
        remaining = self.remaining_seconds()
        if self.state not in LEVEL_STATES:
            return "silent"
        if remaining <= 10:
            return "urgent"
        if remaining <= 20:
            return "tension"
        return "normal"

    def _handle_menu_input(self, event_name):
        # 處理主選單上下移動與確認，決定進入遊戲、排行榜或音量設定。
        if event_name == EVENT_UP:
            self.menu_index = (self.menu_index - 1) % len(self.menu_items)
            self._queue_sound(SOUND_KEY)
        elif event_name == EVENT_DOWN:
            self.menu_index = (self.menu_index + 1) % len(self.menu_items)
            self._queue_sound(SOUND_KEY)
        elif event_name == EVENT_CONFIRM:
            self._queue_sound(SOUND_KEY)
            if self.menu_index == 0:
                self.start_game()
            elif self.menu_index == 1:
                self.state = STATE_RANK
            else:
                self.state = STATE_SETTING

    def _handle_level_input(self, event_name):
        # 處理遊戲中移動與暫停；碰撞和過關都集中由移動流程判斷。
        if event_name == EVENT_BACK:
            self.previous_state = self.state
            self.state = STATE_PAUSE
            self.pause_index = 0
            self._queue_sound(SOUND_KEY)
            return

        movement = {
            EVENT_UP: (0, -1),
            EVENT_DOWN: (0, 1),
            EVENT_LEFT: (-1, 0),
            EVENT_RIGHT: (1, 0),
        }.get(event_name)

        if movement is not None:
            self._move_player(movement[0], movement[1])

    def _handle_pause_input(self, event_name):
        # 處理暫停畫面的選項，讓玩家可以繼續原關卡或回主選單。
        if event_name == EVENT_UP:
            self.pause_index = (self.pause_index - 1) % len(self.pause_items)
            self._queue_sound(SOUND_KEY)
        elif event_name == EVENT_DOWN:
            self.pause_index = (self.pause_index + 1) % len(self.pause_items)
            self._queue_sound(SOUND_KEY)
        elif event_name == EVENT_BACK:
            self.state = self.previous_state
            self._queue_sound(SOUND_KEY)
        elif event_name == EVENT_CONFIRM:
            self._queue_sound(SOUND_KEY)
            if self.pause_index == 0:
                self.state = self.previous_state
            else:
                self._return_to_menu()

    def _handle_finish_input(self, event_name):
        # 結算畫面只等待確認或返回，按下後回到主選單。
        if event_name in (EVENT_CONFIRM, EVENT_BACK):
            self._queue_sound(SOUND_KEY)
            self._return_to_menu()

    def _handle_rank_input(self, event_name):
        # 排行榜畫面不改分數，只讓確認或返回鍵回主選單。
        if event_name in (EVENT_CONFIRM, EVENT_BACK):
            self._queue_sound(SOUND_KEY)
            self.state = STATE_MENU

    def _handle_setting_input(self, event_name):
        # 音量設定用左右調整 0 到 100，確認或返回後回主選單。
        if event_name == EVENT_LEFT:
            self.volume = self._clamp(self.volume - 10, 0, 100)
            self._queue_sound(SOUND_KEY)
        elif event_name == EVENT_RIGHT:
            self.volume = self._clamp(self.volume + 10, 0, 100)
            self._queue_sound(SOUND_KEY)
        elif event_name in (EVENT_CONFIRM, EVENT_BACK):
            self._queue_sound(SOUND_KEY)
            self.state = STATE_MENU

    def start_game(self):
        # 開始新遊戲時重置分數、時間與關卡，再載入第一關。
        self.total_score = 0
        self.final_score = 0
        self.finish_success = False
        self.total_elapsed_ms = 0
        self.level_index = 0
        self._enter_level(0)

    def _enter_level(self, level_index):
        # 載入指定關卡，設定 FSM 狀態、玩家起點與本關倒計時。
        self.level_index = level_index
        self.state = (STATE_LEVEL_1, STATE_LEVEL_2, STATE_LEVEL_3)[level_index]
        self.player_x, self.player_y = START_POINTS[level_index]
        self.level_elapsed_ms = 0
        self.last_update_ms = ticks_ms()

    def _move_player(self, delta_x, delta_y):
        # 嘗試移動玩家一格；只有目標不是牆壁時才更新座標。
        next_x = self.player_x + delta_x
        next_y = self.player_y + delta_y
        if not self._is_walkable(next_x, next_y):
            return

        self.player_x = next_x
        self.player_y = next_y
        if (self.player_x, self.player_y) == END_POINTS[self.level_index]:
            self._complete_level()

    def _complete_level(self):
        # 完成本關時計分，若還有下一關就切換關卡，最後一關則進入結算。
        self.total_score += self.current_level_score()
        self._queue_sound(SOUND_LEVEL_CLEAR)

        if self.level_index >= len(LEVEL_MAPS) - 1:
            self._finish_game(True)
        else:
            self.total_elapsed_ms += self.level_elapsed_ms
            self._enter_level(self.level_index + 1)

    def _finish_game(self, success):
        # 結束遊戲並標記要儲存分數，成功或失敗會排入不同結算音效。
        if self.state in LEVEL_STATES:
            self.total_elapsed_ms += self.level_elapsed_ms
        self.finish_success = success
        self.final_score = self.total_score
        self.state = STATE_FINISH
        self.needs_score_save = True
        self._queue_sound(SOUND_WIN if success else SOUND_LOSE)

    def _return_to_menu(self):
        # 回主選單時只重置畫面狀態，不清除 Flash 中的分數紀錄。
        self.state = STATE_MENU
        self.menu_index = 0
        self.level_index = 0
        self.level_elapsed_ms = 0
        self.last_update_ms = ticks_ms()

    def _is_walkable(self, x_position, y_position):
        # 檢查地圖座標是否可走，越界或牆壁都不能讓玩家進入。
        maze = LEVEL_MAPS[self.level_index]
        if y_position < 0 or y_position >= len(maze):
            return False
        if x_position < 0 or x_position >= len(maze[y_position]):
            return False
        return maze[y_position][x_position] != "#"

    def _queue_sound(self, sound_name):
        # 把音效名稱放入佇列，讓遊戲邏輯不用等待蜂鳴器播放完。
        self.sound_events.append(sound_name)

    def _clamp(self, value, low, high):
        # 將數值限制在 low 到 high 之間，避免音量或分數計算超出範圍。
        if value < low:
            return low
        if value > high:
            return high
        return value
