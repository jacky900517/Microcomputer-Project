from code.config import (
    MAP_CELL_SIZE,
    MAP_LEFT,
    MAP_TOP,
    OLED_ADDRESS,
    OLED_I2C_ID,
    PIN_OLED_SCL,
    PIN_OLED_SDA,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STATE_FINISH,
    STATE_LEVEL_1,
    STATE_LEVEL_2,
    STATE_LEVEL_3,
    STATE_MENU,
    STATE_PAUSE,
    STATE_RANK,
    STATE_SETTING,
)


class DisplayUnit:
    def __init__(self):
        # 初始化 OLED；若在電腦端沒有 machine/ssd1306，就改用 console 模式方便檢查。
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.oled = None
        self.console = False
        self.last_frame = None

        try:
            from machine import I2C, Pin
            import code.ssd1306 as ssd1306

            i2c = I2C(
                OLED_I2C_ID,
                sda=Pin(PIN_OLED_SDA),
                scl=Pin(PIN_OLED_SCL),
                freq=400000,
            )
            self.oled = ssd1306.SSD1306_I2C(
                self.width,
                self.height,
                i2c,
                addr=OLED_ADDRESS,
            )
        except Exception:
            self.console = True

    def render(self, snapshot):
        # 依照 snapshot 的 state 選擇畫面，畫面資料不直接讀取或修改 GameEngine。
        frame_key = str(snapshot)
        if frame_key == self.last_frame:
            return
        self.last_frame = frame_key

        state = snapshot.get("state")
        if state == STATE_MENU:
            self.draw_menu(snapshot)
        elif state in (STATE_LEVEL_1, STATE_LEVEL_2, STATE_LEVEL_3):
            self.draw_game(snapshot)
        elif state == STATE_PAUSE:
            self.draw_pause(snapshot)
        elif state == STATE_FINISH:
            self.draw_finish(snapshot)
        elif state == STATE_RANK:
            self.draw_rank(snapshot)
        elif state == STATE_SETTING:
            self.draw_setting(snapshot)

    def draw_menu(self, snapshot):
        # 繪製主選單，包含標題、角色小圖示與目前選取的選項。
        if self.console:
            self._console("MENU", snapshot.get("menu_items"), snapshot.get("menu_index"))
            return

        self._clear()
        self._text("MAZE QUEST", 24, 4)
        self._hline(16, 15, 96, 1)
        self._draw_player_icon(8, 38, 1)
        self._draw_ground()

        items = snapshot.get("menu_items", ())
        selected_index = snapshot.get("menu_index", 0)
        item_left = 32
        max_item_chars = (self.width - item_left) // 8
        for row_index, item in enumerate(items):
            prefix = ">" if row_index == selected_index else " "
            self._text(prefix + self._fit(item, max_item_chars - 1), item_left, 24 + row_index * 12)

        self._show()

    def draw_game(self, snapshot):
        # 繪製遊戲中畫面，把關卡、時間、分數、迷宮、玩家與出口放在同一頁。
        if self.console:
            title = "LEVEL {} T{} S{}".format(
                snapshot.get("level_number"),
                snapshot.get("remaining_seconds"),
                snapshot.get("total_score"),
            )
            self._console(title, (), 0)
            return

        self._clear()
        header = "L{} T{:02d} S{:03d}".format(
            snapshot.get("level_number", 1),
            snapshot.get("remaining_seconds", 0),
            snapshot.get("total_score", 0),
        )
        self._text(header, 0, 0)
        self._draw_maze(snapshot)
        self._show()

    def draw_pause(self, snapshot):
        # 繪製暫停畫面，讓玩家選擇繼續遊戲或回主選單。
        if self.console:
            self._console("PAUSE", snapshot.get("pause_items"), snapshot.get("pause_index"))
            return

        self._clear()
        self._text("PAUSE", 44, 8)
        self._hline(28, 20, 72, 1)
        items = snapshot.get("pause_items", ())
        selected_index = snapshot.get("pause_index", 0)
        for row_index, item in enumerate(items):
            prefix = ">" if row_index == selected_index else " "
            self._text(prefix + item, 28, 30 + row_index * 12)
        self._show()

    def draw_finish(self, snapshot):
        # 繪製結算畫面，顯示通關狀態、時間、分數、最高分與返回提示。
        if self.console:
            self._console("FINISH", ("SCORE {}".format(snapshot.get("final_score", 0)),), 0)
            return

        self._clear()
        success = snapshot.get("finish_success", False)
        title = "FINISH" if success else "TIME OUT"
        top_scores = snapshot.get("top_scores", [])
        high_score = top_scores[0] if top_scores else snapshot.get("final_score", 0)
        self._text(title, 34 if success else 28, 4)
        self._hline(8, 14, 112, 1)
        self._text("TIME  {:02d}:{:02d}".format(snapshot.get("elapsed_seconds", 0) // 60, snapshot.get("elapsed_seconds", 0) % 60), 8, 18)
        self._text("SCORE {:05d}".format(snapshot.get("final_score", 0)), 8, 30)
        self._text("HIGH  {:05d}".format(high_score), 8, 42)
        self._hline(8, 52, 112, 1)
        self._text("A/B TO MENU", 20, 55)
        self._show()

    def draw_rank(self, snapshot):
        # 繪製排行榜，固定顯示最高五筆與最後一次遊戲分數。
        if self.console:
            self._console("RANK", snapshot.get("top_scores", ()), 0)
            return

        self._clear()
        self._text("-- HIGH SCORES --", 0, 0)
        top_scores = snapshot.get("top_scores", [])
        for score_index in range(5):
            score = top_scores[score_index] if score_index < len(top_scores) else 0
            self._text("{}. {:05d}".format(score_index + 1, score), 20, 12 + score_index * 9)
        self._text("LAST {:05d}".format(snapshot.get("last_score", 0)), 20, 56)
        self._show()

    def draw_setting(self, snapshot):
        # 繪製音量設定畫面，用百分比與進度條讓目前音量容易判讀。
        if self.console:
            self._console("VOLUME {}".format(snapshot.get("volume", 0)), (), 0)
            return

        volume = snapshot.get("volume", 0)
        self._clear()
        self._text("VOLUME", 38, 8)
        self._text("{:3d}%".format(volume), 46, 22)
        self._rect(14, 40, 100, 10, 1)
        fill_width = int(volume * 98 // 100)
        self._fill_rect(15, 41, fill_width, 8, 1)
        self._text("<       >", 28, 54)
        self._show()

    def _draw_maze(self, snapshot):
        # 依照字串地圖逐格畫牆壁，再補上出口與玩家，避免手寫大量座標。
        maze = snapshot.get("maze", ())
        player_x, player_y = snapshot.get("player", (0, 0))
        exit_x, exit_y = snapshot.get("exit", (0, 0))

        for row_index, row_text in enumerate(maze):
            for column_index, tile in enumerate(row_text):
                left = MAP_LEFT + column_index * MAP_CELL_SIZE
                top = MAP_TOP + row_index * MAP_CELL_SIZE
                if tile == "#":
                    self._fill_rect(left, top, MAP_CELL_SIZE - 1, MAP_CELL_SIZE - 1, 1)

        self._draw_exit_tile(exit_x, exit_y)
        self._draw_player_tile(player_x, player_y)

    def _draw_player_tile(self, player_x, player_y):
        # 將玩家畫在迷宮格子內，用比格子小的方塊避免和牆壁黏在一起。
        left = MAP_LEFT + player_x * MAP_CELL_SIZE + 1
        top = MAP_TOP + player_y * MAP_CELL_SIZE + 1
        self._fill_rect(left, top, MAP_CELL_SIZE - 2, MAP_CELL_SIZE - 2, 1)

    def _draw_exit_tile(self, exit_x, exit_y):
        # 將出口畫成門框，讓玩家可以在迷宮中看出終點位置。
        left = MAP_LEFT + exit_x * MAP_CELL_SIZE
        top = MAP_TOP + exit_y * MAP_CELL_SIZE
        self._rect(left + 1, top, MAP_CELL_SIZE - 2, MAP_CELL_SIZE - 1, 1)
        self._hline(left + 2, top + MAP_CELL_SIZE - 2, MAP_CELL_SIZE - 4, 0)

    def _draw_player_icon(self, left, top, scale):
        # 用簡單矩形畫角色圖示，避免額外圖片資源並保持 SSD1306 可顯示。
        size = 4 * scale
        self._fill_rect(left + size, top, size * 2, size, 1)
        self._rect(left + size, top + size, size * 2, size * 2, 1)
        self._fill_rect(left, top + size * 2, size, size, 1)
        self._fill_rect(left + size * 3, top + size * 2, size, size, 1)
        self._fill_rect(left + size, top + size * 3, size, size, 1)
        self._fill_rect(left + size * 2, top + size * 3, size, size, 1)

    def _draw_exit_icon(self, left, top):
        # 保留較大的門圖示函式，若之後要恢復圖像式結算畫面可以重用。
        self._rect(left, top + 2, 20, 18, 1)
        self._rect(left + 4, top + 6, 12, 14, 1)
        self._fill_rect(left + 16, top + 12, 2, 2, 1)

    def _draw_ground(self):
        # 在主選單底部畫地面線，讓畫面不會只有文字而顯得空。
        self._hline(0, 58, self.width, 1)
        for dot_x in range(0, self.width, 12):
            self._fill_rect(dot_x, 61, 2, 1, 1)

    def _clear(self):
        # 清除 OLED 緩衝區，避免上一個畫面的像素殘留。
        self.oled.fill(0)

    def _show(self):
        # 將目前緩衝區送到 OLED，所有繪圖完成後才呼叫以減少閃爍。
        self.oled.show()

    def _text(self, text, left, top):
        # 統一文字繪製入口，方便之後若要調整字體或裁切時集中修改。
        self.oled.text(str(text), left, top)

    def _hline(self, left, top, width, color):
        # 畫水平線；若驅動沒有 hline，就退回用 line 畫。
        if width <= 0:
            return
        if hasattr(self.oled, "hline"):
            self.oled.hline(left, top, width, color)
        else:
            self.oled.line(left, top, left + width - 1, top, color)

    def _rect(self, left, top, width, height, color):
        # 畫矩形外框；若驅動沒有 rect，就用四條線組合。
        if width <= 0 or height <= 0:
            return
        if hasattr(self.oled, "rect"):
            self.oled.rect(left, top, width, height, color)
            return
        self._hline(left, top, width, color)
        self._hline(left, top + height - 1, width, color)
        self._vline(left, top, height, color)
        self._vline(left + width - 1, top, height, color)

    def _fill_rect(self, left, top, width, height, color):
        # 畫填滿矩形；若驅動沒有 fill_rect，就逐列畫水平線。
        if width <= 0 or height <= 0:
            return
        if hasattr(self.oled, "fill_rect"):
            self.oled.fill_rect(left, top, width, height, color)
            return
        for row_offset in range(height):
            self._hline(left, top + row_offset, width, color)

    def _vline(self, left, top, height, color):
        # 畫垂直線；若驅動沒有 vline，就退回用 line 畫。
        if height <= 0:
            return
        if hasattr(self.oled, "vline"):
            self.oled.vline(left, top, height, color)
        else:
            self.oled.line(left, top, left, top + height - 1, color)

    def _fit(self, text, max_chars):
        # 將文字裁到指定字數內，避免 SSD1306 文字超出 128px 螢幕。
        text_value = str(text)
        if len(text_value) <= max_chars:
            return text_value
        return text_value[:max_chars]

    def _console(self, title, items, selected_index):
        # 沒有 OLED 硬體時印到終端機，方便在電腦端檢查畫面資料。
        print("[{}]".format(title))
        for item_index, item in enumerate(items or ()):
            prefix = ">" if item_index == selected_index else " "
            print("{} {}".format(prefix, item))
