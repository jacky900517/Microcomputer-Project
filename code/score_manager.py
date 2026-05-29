try:
    import ujson as json
except ImportError:
    import json

from code.config import SCORE_FILE, TOP_SCORE_COUNT


class ScoreManager:
    def __init__(self, filename=SCORE_FILE):
        # 記住分數檔名，之後讀寫 Flash 都集中使用同一個 JSON 檔案。
        self.filename = filename

    def load_scores(self):
        # 從 Flash 讀取分數；若檔案不存在或格式錯誤，就回傳空排行榜。
        try:
            with open(self.filename, "r") as score_file:
                data = json.loads(score_file.read())
        except (OSError, ValueError):
            data = self._default_records()

        top_scores = data.get("top_scores", [])
        last_score = int(data.get("last_score", 0))
        cleaned_scores = self._clean_scores(top_scores)
        return {
            "top_scores": cleaned_scores[:TOP_SCORE_COUNT],
            "last_score": last_score,
        }

    def save_score(self, score):
        # 儲存本局分數，並重新排序最高五筆，確保關機後紀錄不會消失。
        records = self.load_scores()
        score_value = int(score)
        top_scores = records["top_scores"] + [score_value]
        top_scores = self._clean_scores(top_scores)
        records = {
            "top_scores": top_scores[:TOP_SCORE_COUNT],
            "last_score": score_value,
        }
        self._write_records(records)
        return records

    def get_top_scores(self):
        # 取得最高五筆分數，提供排行榜畫面顯示。
        return self.load_scores()["top_scores"]

    def get_last_score(self):
        # 取得最後一次遊戲分數，讓排行榜可以顯示最近一局結果。
        return self.load_scores()["last_score"]

    def _default_records(self):
        # 建立預設資料結構，第一次執行或分數檔壞掉時使用。
        return {"top_scores": [], "last_score": 0}

    def _clean_scores(self, scores):
        # 將讀到的分數轉成整數並由高到低排序，避免 JSON 資料型態不一致。
        cleaned_scores = []
        for score in scores:
            try:
                cleaned_scores.append(int(score))
            except (TypeError, ValueError):
                pass
        cleaned_scores.sort(reverse=True)
        return cleaned_scores

    def _write_records(self, records):
        # 將排行榜資料寫回 Flash，集中處理檔案寫入避免其他模組直接碰檔案。
        with open(self.filename, "w") as score_file:
            score_file.write(json.dumps(records))
