import os
import sys
from pathlib import Path
import sqlite3
import threading
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import Optional, Tuple

import models  #  nlp sentencetranformers 

# --- การตัังค่า path สำหรับเก็บฐานข้อมูล ---------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / "data" / "FQA_data.db"
_model_lock = threading.Lock()

# --- CONFIG ------------------------------------------------------------
THRESHOLD = 0.50  # <-- คสำหรับการ match intent ถ้าคะแนน cosine similarity ต่ำกว่านี้จะถือว่าไม่ match
intent_data: dict = {}

# schema ของแต่ละภาษาใน DB
_TABLE_SCHEMA = {
    "th":      ("intents_th",  "tag_th",  "patterns_th",  "response_th"),
    "my":      ("intents_mya", "tag_mya", "patterns_mya", "response_mya"),
    "chinese": ("intents_ch",  "tag_ch",  "patterns_ch",  "response_ch"),
}

# --- ข้อความ fallback ------------------------------------------------------------------
FALLBACK_MAP = {
    "vits_tha": "ขอโทษด้วยนะฉันไม่เข้าใจที่คุณหมายถึง",
    "vits_mya": "တောင်းပန်ပါတယ်၊ ခင်ဗျား ဘာပြောချင်တာလဲဆိုတာ ကျွန်တော် နားမလည်ပါဘူး။",
    "sherpa_zh": "抱歉，我不明白您的意思。",
}

def load_intents(log_cb=print) -> None:
    if models.nlp_model is None:
        log_cb("ไม่สามารถโหลด intents ได้ควรเรียก models.load_models() ก่อน)")
        return

    log_cb("โหลดฐานข้อมูลและทำการคำนวณ Embeddings...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cur  = conn.cursor()
    except sqlite3.Error as e:
        log_cb(f"เชื่อมต่อฐานข้อมูล {DB_PATH} ไม่สำเร็จ: {e}")
        return

    for lang, (tbl, t_col, p_col, r_col) in _TABLE_SCHEMA.items():
        try:
            cur.execute(f"SELECT {t_col}, {p_col}, {r_col} FROM {tbl}")
            rows = cur.fetchall()
        except sqlite3.OperationalError as e:
            log_cb(f"⚠️ ไม่พบตาราง {tbl}: {e}")
            intent_data[lang] = []
            continue

        if not rows:
            intent_data[lang] = []
            continue

        tags       = [r[0] for r in rows]
        patterns   = [r[1] for r in rows]
        responses  = [r[2] for r in rows]
        with _model_lock:
            embeddings = models.nlp_model.encode(patterns, convert_to_numpy=True)

        intent_data[lang] = [
            {
                "tag":      tags[i],
                "pattern":  patterns[i],
                "emb":      embeddings[i].reshape(1, -1),
                "response": responses[i],
            }
            for i in range(len(rows))
        ]

    conn.close()
    log_cb("พร้อมใช้งาน")


def match_intent(lang_code: str, text: str) -> Tuple[Optional[str], float, Optional[str], Optional[str]]:
    normalized_lang = {"burmese": "my", "zh": "chinese"}.get(lang_code, lang_code)
    data = intent_data.get(normalized_lang, intent_data.get(lang_code, []))
    if not data:
        return None, 0.0, None, None

    # กัน crash เผื่อมีการเรียกใช้ก่อน models.load_models() โหลดเสร็จ
    if models.nlp_model is None:
        return None, 0.0, None, None

    if not text or not text.strip():
        return None, 0.0, None, None

    with _model_lock:
        vec = models.nlp_model.encode([text], convert_to_numpy=True)

    # embedding ของ pattern เป็น matrix เดียวแล้วคำนวณ cosine similarity
    all_embs = np.vstack([item["emb"] for item in data])
    scores = cosine_similarity(vec, all_embs)[0]
    best_idx = int(np.argmax(scores))
    best_score = float(scores[best_idx])
    best_resp = data[best_idx]["response"]
    best_tag = data[best_idx]["tag"]
    best_pattern = data[best_idx].get("pattern", "")

    if best_score >= THRESHOLD:
        return best_resp, best_score, best_tag, best_pattern
    return None, best_score, None, best_pattern

# --- แสดงข้อความ fallback เมือ่ไม่พบ intent ที่ตรงกับข้อความผู้ใช้ -----------------------
def get_fallback(tts_mode: str) -> str:
    return FALLBACK_MAP.get(tts_mode, "...")
