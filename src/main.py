import os
import sys
import traceback
from pathlib import Path

# เพิ่มโฟลเดอร์ src เข้าไปใน Python Path
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    SRC_DIR = Path(__file__).resolve().parent
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    BASE_DIR = SRC_DIR.parent

os.chdir(BASE_DIR)

FFMPEG_DIR = BASE_DIR / "ffmpeg"
if FFMPEG_DIR.exists():
    os.environ["PATH"] = str(FFMPEG_DIR) + os.pathsep + os.environ.get("PATH", "")

MODELS_CACHE   = BASE_DIR / "models_cache"
DATA_DIR       = BASE_DIR / "data"
ASSETS_DIR     = BASE_DIR / "assets"
TEMP_AUDIO_DIR = ASSETS_DIR / "temp_audio"
DB_PATH        = DATA_DIR / "FQA_data.db"
DICT_PATH      = DATA_DIR / "data_dictionary.csv"

REQUIRED_DIRS = [
    MODELS_CACHE,
    MODELS_CACHE / "huggingface",
    MODELS_CACHE / "whisper",
    MODELS_CACHE / "sherpa",
    MODELS_CACHE / "pythainlp-data",
    DATA_DIR,
    ASSETS_DIR / "image",
    TEMP_AUDIO_DIR,
]

def ensure_directories(log_cb=print) -> None:
    for d in REQUIRED_DIRS:
        d.mkdir(parents=True, exist_ok=True)

    if not DB_PATH.exists():
        log_cb(f"ไม่พบไฟล์ฐานข้อมูล {DB_PATH}")

    if not DICT_PATH.exists():
        log_cb(f"ไม่พบไฟล์ Data Dictionary {DICT_PATH}")

def main() -> None:
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    import customtkinter as ctk
    from gui import ChatbotGUI
    root = ctk.CTk()
    ChatbotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    try:
        ensure_directories()
        main()
    except Exception as e:
        err_msg = traceback.format_exc()
        try:
            with open(BASE_DIR / "error_log.txt", "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass

        print("=" * 60)
        print("โปรแกรมไม่สามารถเริ่มทำงานได้")
        print("รายละเอียดสำหรับผู้ดูแลระบบ:")
        print(err_msg)
        print("=" * 60)

        try:
            import tkinter.messagebox as mb
            mb.showerror("DJOP_DEMO Error", f"โปรแกรมไม่สามารถเริ่มทำงานได้:\n\n{e}\n\nตรวจสอบรายละเอียดเพิ่มเติมได้ที่ไฟล์ error_log.txt")
        except Exception:
            pass
        sys.exit(1)
