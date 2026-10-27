# 🤖 DJOP Multilingual VoiceBot (ระบบผู้ช่วยโต้ตอบด้วยเสียงสำหรับให้คำปรึกษาด้านความเครียดเบื้องต้น)

**สถานพินิจและคุ้มครองเด็กและเยาวชนจังหวัดตาก กรมพินิจและคุ้มครองเด็กและเยาวชน (DJOP)**  
Department of Juvenile Observation and Protection, Tak Province

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.5.1%2Bcu121-ee4c2c.svg)](https://pytorch.org/)
[![UI](https://img.shields.io/badge/GUI-CustomTkinter%206.0-green.svg)](https://customtkinter.tomschimansky.com/)
[![Whisper STT](https://img.shields.io/badge/STT-OpenAI%20Whisper-orange.svg)](https://github.com/openai/whisper)
[![Offline Mode](https://img.shields.io/badge/Operation-100%25%20Offline-brightgreen.svg)]()
[![Languages](https://img.shields.io/badge/Languages-TH%20%7C%20MY%20%7C%20ZH-lightgrey.svg)]()

---

## 📌 บทนำและวัตถุประสงค์ของโครงการ (Overview)

**DJOP Multilingual VoiceBot** เป็นระบบผู้ช่วยปัญญาประดิษฐ์แบบโต้ตอบด้วยเสียง (Voice-to-Voice) ที่พัฒนาขึ้นเพื่อให้บริการเยาวชนและผู้รับบริการของ **สถานพินิจและคุ้มครองเด็กและเยาวชนจังหวัดตาก** เพื่อทำหน้าที่เป็นเพื่อนรับฟัง ให้คำแนะนำ ตอบข้อสงสัย และช่วยคลายความกังวลหรือความเครียดเบื้องต้น

> 📖 **สำหรับคู่มือการใช้งานแบบละเอียดสำหรับเจ้าหน้าที่และผู้ใช้ทั่วไป:**  
> โปรดอ่านเอกสารฉบับเต็มได้ที่ [USER_MANUAL.md](USER_MANUAL.md) (ประกอบด้วยขั้นตอนการใช้งาน, การสังเกตพฤติกรรมเยาวชน, การแก้ปัญหาเบื้องต้น และรายการ 30 หมวดหมู่หัวข้อคำปรึกษา)

---

## ✨ คุณสมบัติเด่น (Key Features)

- 🌐 **รองรับ 3 ภาษา (Multilingual Support):**
  - ภาษาไทย (Thai - 🇹🇭)
  - ภาษาเมียนมา (Myanmar - 🇲🇲)
  - ภาษาจีน (Chinese - 🇨🇳)
- 🔒 **ทำงานแบบ Offline 100% (High Privacy & Security):**
  - ทำงานและประมวลผลโมเดล AI ทั้งหมดบนเครื่องคอมพิวเตอร์ในพื้นที่ (Local Inference)
  - ไม่มีการส่งข้อมูลเสียง ข้อความ หรือประวัติใด ๆ ออกไปยังคลาวด์หรือภายนอกระบบ เพื่อความปลอดภัยสูงสุดของข้อมูลเยาวชน
- 🎙️ **โต้ตอบด้วยเสียงพูดครบวงจร (Voice-to-Voice Pipeline):**
  - **Speech-to-Text (STT):** แปลงเสียงพูดเป็นข้อความด้วยโมเดล Whisper (`biodatlab/whisper-th-medium-combined` สำหรับภาษาไทย และ `chuuhtetnaing/whisper-small-myanmar` สำหรับภาษาเมียนมา)
  - **Data Normalization / Dictionary:** แก้ไขคำผิดจากการถอดเสียงด้วยระบบพจนานุกรมเทียบเคียงคำอัตโนมัติ
  - **Intent & Semantic Search:** ทำความเข้าใจเจตนาของผู้พูดด้วยโมเดล `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` และเปรียบเทียบ Cosine Similarity หาคำตอบที่ตรงใจที่สุด
  - **Text-to-Speech (TTS):** สังเคราะห์เสียงพูดตอบกลับที่เป็นธรรมชาติ (PyThaiTTS/ONNX ภาษาไทย, Facebook MMS-TTS ภาษาเมียนมา, Sherpa-ONNX ภาษาจีน)
- 🖥️ **ส่วนติดต่อผู้ใช้สไตล์ Kiosk เต็มหน้าจอ (Fullscreen Kiosk GUI):**
  - ออกแบบด้วย `CustomTkinter` รองรับหน้าจอสัมผัส (Touchscreen) ใช้งานง่ายด้วยปุ่มกดพูดแบบ Hold-to-Talk
  - มีระบบไฟแสดงสถานะการโหลดโมเดล (กำลังโหลด / พร้อม)
  - มีปุ่ม "🔊 ฟังอีกครั้ง" (Replay) และปุ่ม "🗘 รีเซ็ต" (Reset) สำหรับล้างประวัติการสนทนาก่อนส่งมอบให้ผู้รับบริการคนถัดไป

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
DJOP_DEMO/
├── assets/                  # ไฟล์รูปภาพ ไอคอน โลโก้ และเสียงชั่วคราว
│   ├── image/              # ภาพธงชาติ (TH, MY, ZH), โลโก้หน่วยงาน, ไอคอนไมโครโฟน
│   └── temp_audio/         # โฟลเดอร์เก็บไฟล์เสียง WAV ชั่วคราวสำหรับการประมวลผล
├── data/                    # โฟลเดอร์ฐานข้อมูลและพจนานุกรม (ดูหมายเหตุด้านล่าง)
│   ├── .gitkeep
│   ├── FQA_data.db         # (Excluded from Git) ฐานข้อมูล SQLite เก็บชุดคำถาม-คำตอบ
│   └── data_dictionary.csv # (Excluded from Git) ข้อมูลพจนานุกรมแก้คำผิด ASR
├── models_cache/            # โฟลเดอร์เก็บน้ำหนักโมเดล AI แบบ Offline (Excluded from Git)
│   ├── .gitkeep
│   ├── huggingface/        # แคชโมเดล Transformers & Sentence-Transformers
│   ├── sherpa/             # โมเดล TTS ภาษาจีน (vits-aishell3)
│   └── whisper/            # โมเดล OpenAI Whisper (small.pt, medium.pt)
├── src/                     # ซอร์สโค้ดหลักของระบบ
│   ├── chat.py             # จัดการเชื่อมต่อฐานข้อมูล intent, คำนวณ Cosine Similarity
│   ├── dictionary.py       # ค้นหาและแทนที่คำผิดตามพจนานุกรม (Data Dictionary)
│   ├── gui.py              # หน้าต่างโปรแกรมหลัก CustomTkinter (Kiosk UI)
│   ├── main.py             # จุดเริ่มต้นรันโปรแกรม (Entry Point)
│   └── models.py           # โมดูลโหลดโมเดล STT, NLP, TTS แบบ Offline
├── voices/                  # โมเดลเสียงสังเคราะห์ TTS ภาษาไทย
│   ├── speaker_config.json # การตั้งค่า Speaker Voice
│   └── th_f_1.onnx         # โมเดลเสียง VITS ภาษาไทย
├── .gitignore               # กำหนดรายการไฟล์ที่ไม่นำขึ้น Git
├── DJOP_DEMO.spec           # ไฟล์คอนฟิกสำหรับการแพ็กโปรแกรมด้วย PyInstaller
├── export_exe.bat           # สคริปต์อัตโนมัติสำหรับการ Build ไฟล์ .exe
├── README.md                # เอกสารแนะนำและคู่มือการติดตั้งโปรเจกต์
├── requirements.txt         # รายการแพ็กเกจ Python และเวอร์ชันที่รองรับ
├── Start_DJOP_DEMO.bat      # ทางลัดสำหรับเปิดโปรแกรมหลัก
└── USER_MANUAL.md           # คู่มือการใช้งานสำหรับเจ้าหน้าที่และผู้รับบริการ
```

> [!NOTE]
> **หมายเหตุเกี่ยวกับโฟลเดอร์ `data/` และ `models_cache/`:**
> - โฟลเดอร์ **`data/`** (`FQA_data.db` และ `data_dictionary.csv`) ไม่ได้ถูกนำขึ้น GitHub เนื่องจากเป็นข้อมูลภายในและเพื่อการปกป้องความเป็นส่วนตัว
> - โฟลเดอร์ **`models_cache/`** ไม่ได้ถูกนำขึ้น GitHub เนื่องจากขนาดไฟล์รวมกว่า 7 GB ซึ่งเกินขีดจำกัดของ GitHub โดยผู้ติดตั้งสามารถดาวน์โหลดหรือวางไฟล์โมเดลตามโครงสร้างที่ระบุไว้ด้านล่าง

---

## 💻 ข้อกำหนดของระบบ (System Requirements)

| รายการ | ข้อกำหนดขั้นต่ำ | ข้อกำหนดที่แนะนำ |
| :--- | :--- | :--- |
| **ระบบปฏิบัติการ** | Windows 10 (64-bit) | Windows 11 (64-bit) |
| **Python** | Python 3.10 หรือ 3.11 | Python 3.10.x (x64) |
| **หน่วยประมวลผล (CPU)** | Intel Core i5 / AMD Ryzen 5 | Intel Core i7 / AMD Ryzen 7 ขึ้นไป |
| **การ์ดแสดงผล (GPU)** | CPU Mode (ทำงานได้) | NVIDIA GPU มี VRAM 6GB+ รองรับ CUDA 12.1 (เพื่อการตอบสนองที่รวดเร็ว) |
| **RAM** | 8 GB | 16 GB ขึ้นไป |
| **เครื่องมือภายนอก** | FFmpeg (จำเป็นสำหรับ Whisper) | FFmpeg เวอร์ชันล่าสุดใน System PATH |
| **อุปกรณ์เสียง** | ไมโครโฟนและลำโพงทั่วไป | ไมโครโฟนตัดเสียงรบกวน (Noise Cancelling) และลำโพงเสียงชัดเจน |

---

## 🛠️ ขั้นตอนการติดตั้งและตั้งค่าระบบ (Installation & Setup)

### 1. โคลน Repository
```powershell
git clone https://github.com/wiraphat-kanin/VoiceBot.git
cd VoiceBot
```

### 2. ติดตั้ง FFmpeg (จำเป็นสำหรับการถอดเสียง)
ระบบถอดเสียง Whisper จำเป็นต้องใช้งาน FFmpeg ในการอ่านและแปลงสัญญาณเสียง:
- **ติดตั้งผ่าน Winget (แนะนำ):**
  ```powershell
  winget install ffmpeg
  ```
- **หรือติดตั้งด้วยตนเอง:** ดาวน์โหลดจาก [gyan.dev/ffmpeg](https://www.gyan.dev/ffmpeg/builds/) และนำโฟลเดอร์ `bin` ไปเพิ่มใน System Environment Variables (`PATH`)

### 3. สร้างและเปิดใช้งาน Virtual Environment
```powershell
# สร้าง venv ด้วย Python 3.10 หรือ 3.11
python -m venv venv

# เปิดใช้งาน venv (PowerShell)
.\venv\Scripts\Activate.ps1

# หรือ Command Prompt (CMD)
.\venv\Scripts\activate.bat
```

### 4. ติดตั้ง PyTorch (CUDA 12.1)
หากเครื่องมี GPU NVIDIA ที่รองรับ CUDA:
```powershell
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
```
*(หากไม่มี GPU NVIDIA ให้รัน: `pip install torch torchvision torchaudio` เพื่อใช้งานบน CPU)*

### 5. ติดตั้ง Dependencies ทั้งหมด
```powershell
pip install -r requirements.txt
```

### 6. จัดเตรียมข้อมูลในโฟลเดอร์ `data/`
สร้างหรือวางไฟล์ฐานข้อมูลและพจนานุกรมในโฟลเดอร์ `data/`:
1. **`data/FQA_data.db`**: ฐานข้อมูล SQLite ที่มีตารางคำถาม-คำตอบรองรับ 3 ภาษา:
   - `intents_th`: คอลัมน์ `tag_th`, `patterns_th`, `response_th`
   - `intents_mya`: คอลัมน์ `tag_mya`, `patterns_mya`, `response_mya`
   - `intents_ch`: คอลัมน์ `tag_ch`, `patterns_ch`, `response_ch`
2. **`data/data_dictionary.csv`**: ตารางคำแก้ ASR มีคอลัมน์:
   - `language`: รหัสภาษา (`th`, `my`, `zh`)
   - `wrong`: คำที่โมเดล ASR มักถอดเสียงผิด
   - `correct`: คำที่ถูกต้องที่ต้องการแปลงแทนที่

### 7. จัดเตรียมโมเดล AI ในโฟลเดอร์ `models_cache/`
ระบบถูกตั้งค่าให้รันแบบ Offline โดยดึงโมเดลจากโฟลเดอร์ `models_cache/`:
- **Whisper Models:** วางไฟล์ `small.pt` หรือ `medium.pt` ใน `models_cache/whisper/`
- **Hugging Face Cache:** โหลดหรือวาง snapshot ของโมเดลต่อไปนี้ใน `models_cache/huggingface/hub/`:
  - `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
  - `biodatlab/whisper-th-medium-combined`
  - `chuuhtetnaing/whisper-small-myanmar`
  - `facebook/mms-tts-mya`
- **Sherpa-ONNX (TTS ภาษาจีน):** วางไฟล์โมเดล `vits-aishell3.onnx`, `lexicon.txt`, `tokens.txt` ใน `models_cache/sherpa/`

---

## 🚀 การเริ่มใช้งานโปรแกรม (Running the Application)

### วิธีที่ 1: รันผ่าน Python
```powershell
python src/main.py
```

### วิธีที่ 2: รันผ่านไฟล์ทางลัด Batch File
ดับเบิลคลิกที่ไฟล์:
```text
Start_DJOP_DEMO.bat
```

### วิธีที่ 3: คอมไพล์เป็นไฟล์ .exe แบบพกพา (Standalone Executable)
หากต้องการ Build โปรแกรมเป็นไฟล์ `.exe` สำหรับนำไปใช้งานโดยไม่ต้องลง Python:
```powershell
.\export_exe.bat
```
*(ไฟล์ `.exe` พร้อมไลบรารีที่จำเป็นจะถูกสร้างไว้ที่ `dist/DJOP_DEMO/DJOP_DEMO.exe`)*

---

## 🧭 การควบคุมและปุ่มลัดในโหมด Kiosk (Shortcuts)

- **ปุ่ม `F11`:** สลับโหมดเต็มหน้าจอ (Toggle Fullscreen)
- **ปุ่ม `Escape` (`Esc`):** ออกจากโหมดเต็มหน้าจอ / ปิดโปรแกรม
- **ปุ่ม `🗘 รีเซ็ต` (บนหน้าจอ):** ล้างประวัติการสนทนาเพื่อเริ่มสนทนากับผู้รับบริการคนใหม่

---

## ⚠️ ข้อพึงระวังและมาตรการความปลอดภัย (Safety & Ethics Notice)

> [!IMPORTANT]
> ระบบนี้ถูกสร้างขึ้นเพื่อเป็น **เครื่องมือช่วยสนับสนุนและคัดกรองเบื้องต้น (First-line Screening)** เท่านั้น **ไม่ใช่การวินิจฉัยทางการแพทย์หรือจิตเวช**
> 
> **ข้อกำหนดการใช้งานในสถานพินิจฯ:**
> 1. การใช้งานต้องอยู่ภายใต้การกำกับดูแลและสังเกตการณ์ของเจ้าหน้าที่อย่างใกล้ชิด
> 2. หากเยาวชนมีสัญญาณความเครียดรุนแรง ความคิดทำร้ายตนเอง หรือประเด็นวิกฤต เจ้าหน้าที่ต้องเข้าแทรกแซงและส่งต่อให้นักจิตวิทยาหรือแพทย์ทันที
> 3. ต้องกดปุ่ม **"รีเซ็ต"** ทุกครั้งหลังจบการสนทนากับผู้รับบริการแต่ละราย เพื่อรักษาความลับและความเป็นส่วนตัวของเด็กและเยาวชน

---

## 👥 หน่วยงานเจ้าของโครงการ (Organization)

- **สถานพินิจและคุ้มครองเด็กและเยาวชนจังหวัดตาก**  
  กรมพินิจและคุ้มครองเด็กและเยาวชน กระทรวงยุติธรรม
