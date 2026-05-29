# OLED 顯示器的解析度設定。
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64

# OLED I2C 腳位與位址，集中管理方便換線時修改。
OLED_I2C_ID = 1
OLED_ADDRESS = 0x3C
PIN_OLED_SDA = 14
PIN_OLED_SCL = 15

# 所有輸入與蜂鳴器 GPIO 腳位，對應 Project.md 的硬體規範。
PIN_JOYSTICK_X = 26
PIN_JOYSTICK_Y = 27
PIN_JOYSTICK_SW = 16
PIN_BUTTON_A = 17
PIN_BUTTON_B = 18
PIN_BUZZER = 19

# 遊戲時間與計分規則，讓 game.py 不需要寫死魔法數字。
LEVEL_TIME_SECONDS = 30
BASE_SCORE = 100
PENALTY_START_SECONDS = 20
PENALTY_PER_SECOND = 5

# 任務更新頻率與硬體去彈跳時間。
INPUT_POLL_MS = 20
GAME_LOOP_MS = 50
JOYSTICK_REPEAT_MS = 160
BUTTON_DEBOUNCE_MS = 180

# 統一輸入事件名稱，讓輸入模組和遊戲模組用同一組語意溝通。
EVENT_UP = "UP"
EVENT_DOWN = "DOWN"
EVENT_LEFT = "LEFT"
EVENT_RIGHT = "RIGHT"
EVENT_CONFIRM = "CONFIRM"
EVENT_BACK = "BACK"

# FSM 狀態名稱，集中定義可以避免不同檔案拼字不一致。
STATE_MENU = "menu"
STATE_LEVEL_1 = "level_1"
STATE_LEVEL_2 = "level_2"
STATE_LEVEL_3 = "level_3"
STATE_PAUSE = "pause"
STATE_FINISH = "finish"
STATE_RANK = "rank"
STATE_SETTING = "setting"

# 三個遊戲關卡狀態常一起判斷，因此另外整理成 tuple。
LEVEL_STATES = (STATE_LEVEL_1, STATE_LEVEL_2, STATE_LEVEL_3)

# 音效事件名稱，GameEngine 只排事件，不直接控制蜂鳴器。
SOUND_KEY = "key"
SOUND_LEVEL_CLEAR = "level_clear"
SOUND_WIN = "win"
SOUND_LOSE = "lose"

# Flash 分數儲存與預設音量設定。
DEFAULT_VOLUME = 60
SCORE_FILE = "scores.json"
TOP_SCORE_COUNT = 5

# OLED 迷宮繪製座標與每格大小。
MAP_CELL_SIZE = 6
MAP_LEFT = 7
MAP_TOP = 14
