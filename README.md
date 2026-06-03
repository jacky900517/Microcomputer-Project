# 第12組

MicroPython 期末專題：掌上型迷宮逃脫遊戲。

## 上傳到 Pico 的檔案

請將本資料夾中的 `.py` 檔案上傳到 Pico / Pico 2 W 的根目錄，入口檔案是 `main.py`。

- `main.py`
- `config.py`
- `game.py`
- `map_data.py`
- `display_unit.py`
- `input_unit.py`
- `joystick.py`
- `score_manager.py`
- `sounds.py`
- `ssd1306.py`

## 硬體腳位

| 元件 | 腳位 |
|---|---|
| OLED SDA | GP14 |
| OLED SCL | GP15 |
| 搖桿 VRx | GP26 |
| 搖桿 VRy | GP27 |
| 搖桿 SW | GP16 |
| 按鈕 A | GP17 |
| 按鈕 B | GP18 |
| 蜂鳴器 + | GP19 |
| 蜂鳴器 - | GND |

## 操作

- 主選單：搖桿上下移動，A 或 SW 確認。
- 遊戲中：搖桿控制玩家移動，B 暫停。
- 暫停畫面：B 繼續，或選擇回主選單。
- 排行榜：A、SW 或 B 回主選單。
- 音量設定：搖桿左右調整音量，A、SW 或 B 回主選單。

## 儲存資料

分數會寫入 Pico Flash 的 `scores.json`，保留最高 5 筆分數與最後一次遊戲分數。
