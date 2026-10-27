import csv
import sys
from pathlib import Path
from typing import List, Dict, Optional

# --- กำหนด path สำหรับไฟล์ Data Dictionary --------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DICT_PATH = DATA_DIR / "data_dictionary.csv"

# Global cache สำหรับเก็บรายการคำศัพท์
_dictionary_cache: Optional[List[Dict[str, str]]] = None

# การแปลงรหัสภาษาให้เป็นมาตรฐานเดียวกัน
LANG_ALIASES = {
    "th": "th",
    "thai": "th",
    "my": "my",
    "mya": "my",
    "burmese": "my",
    "zh": "zh",
    "ch": "zh",
    "chinese": "zh",
}

# แปลงรหัสภาษาให้อยู่ในรูปแบบมาตรฐาน th, my, zh
def normalize_lang_code(lang_code: Optional[str]) -> Optional[str]:
    if not lang_code:
        return None
    cleaned = lang_code.strip().lower()
    return LANG_ALIASES.get(cleaned, cleaned)

def load_dictionary(csv_path: Optional[Path | str] = None, force_reload: bool = False) -> List[Dict[str, str]]:

    # โหลดข้อมูล Data Dictionary จากไฟล์ CSV
    # รองรับการเปิดไฟล์แบบ utf-8-sig รองรับทั้ง UTF-8 ทั่วไป และ UTF-8 BOM จาก Excel
    # เรียงลำดับคำผิด wrong ตามความยาวจากยาวไปสั้น Length-Descending
    # เพื่อป้องกันปัญหาการแทนที่คำสั้นทับซ้อนกับวลียาว
    global _dictionary_cache
    if _dictionary_cache is not None and not force_reload:
        return _dictionary_cache

    file_path = Path(csv_path) if csv_path else DEFAULT_DICT_PATH
    rules: List[Dict[str, str]] = []

    if not file_path.exists():
        # หากไม่พบไฟล์จะคืนค่าลิสต์ว่าง และแจ้งเตือน
        print(f"ไม่พบไฟล์ Data Dictionary ที่: {file_path}")
        _dictionary_cache = rules
        return _dictionary_cache

    try:
        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            # ตรวจสอบชื่อ column แบบยืดหยุ่นตัด space และ ตัวพิมพ์เล็ก
            if reader.fieldnames:
                field_map = {name.strip().lower(): name for name in reader.fieldnames}
                wrong_col = field_map.get("wrong")
                correct_col = field_map.get("correct")
                lang_col = field_map.get("language", field_map.get("lang"))

                if wrong_col and correct_col:
                    for row in reader:
                        wrong = (row.get(wrong_col) or "").strip()
                        correct = (row.get(correct_col) or "").strip()
                        lang = (row.get(lang_col) or "").strip().lower() if lang_col else ""

                        # ข้ามแถวที่ว่างหรือขึ้นต้นด้วยคอมเมนต์ 
                        if not wrong or wrong.startswith("#"):
                            continue

                        rules.append({
                            "wrong": wrong,
                            "correct": correct,
                            "language": normalize_lang_code(lang) or lang,
                        })

        # จัดลำดับความยาวของ wrong จากยาวที่สุดไปหาสั้นที่สุด **สำคัญมากสำหรับภาษาที่ไม่มีการเว้นวรรค**
        rules.sort(key=lambda item: len(item["wrong"]), reverse=True)
        _dictionary_cache = rules
        print(f"โหลด Data Dictionary สำเร็จทั้งหมด {len(rules)} รายการจาก {file_path.name}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดขณะโหลด Data Dictionary: {e}")
        _dictionary_cache = rules

    return _dictionary_cache


def reload_dictionary(csv_path: Optional[Path | str] = None) -> List[Dict[str, str]]:
    # บังคับโหลด Data Dictionary ใหม่จากไฟล์ ใช้เมื่อมีการอัปเดตไฟล์ CSV
    return load_dictionary(csv_path=csv_path, force_reload=True)


def correct_text(text: str, lang_code: Optional[str] = None) -> str:
    
    # แก้ไขข้อความโดยแทนที่เฉพาะคำหรือข้อความที่ผิดตาม Data Dictionary
    # แทนที่เฉพาะคำ/วลีที่ผิดภายในประโยค โดยไม่เปลี่ยนโครงสร้างส่วนอื่น
    # รองรับหลายคำผิดในประโยคเดียวกัน
    # เรียงลำดับคำยาวก่อนคำสั้น ป้องกันการแทนคำผิดตำแหน่ง
    # รองรับข้อความผสมหลายภาษา Mixed Language
    # หากไม่พบคำผิดจะคืนค่าข้อความเดิมโดยไม่สูญหาย
    if not text or not isinstance(text, str):
        return text

    rules = load_dictionary()
    if not rules:
        return text

    target_lang = normalize_lang_code(lang_code)

    # หากมีการระบุภาษาให้จัดลำดับกฎของภาษานั้นขึ้นมาตรวจก่อน แล้วตามด้วยกฎภาษาอื่น
    # เพื่อรองรับทั้งภาษากลุ่มหลักและข้อความที่มีหลายภาษาผสมกัน
    if target_lang:
        primary_rules = [r for r in rules if r["language"] == target_lang or not r["language"]]
        secondary_rules = [r for r in rules if r["language"] != target_lang and r["language"]]
        ordered_rules = primary_rules + secondary_rules
    else:
        ordered_rules = rules

    result = text
    for rule in ordered_rules:
        wrong = rule["wrong"]
        correct = rule["correct"]
        if wrong in result:
            result = result.replace(wrong, correct)

    return result
