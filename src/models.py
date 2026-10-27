import os
import sys
from pathlib import Path
import threading
import numpy as np
import torch
import whisper
from sentence_transformers import SentenceTransformer

# --- การตั้งค่า path สำหรับเก็บโมเดลและไฟล์เสียงชั่วคราว ------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models_cache"
ASSETS_DIR = BASE_DIR / "assets"
TEMP_AUDIO_DIR = ASSETS_DIR / "temp_audio"
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

os.environ["HF_HOME"] = str(MODELS_DIR / "huggingface")
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(MODELS_DIR / "huggingface")
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["PYTHAINLP_DATA"] = str(MODELS_DIR / "pythainlp-data")

# whisper fintune model โหลดผ่าน transformers เพราะเป็นโมเดลจาก HF Hub จำเป็นต้องโหลดใน cahche ของ huggingface 
MODEL_ID = "chuuhtetnaing/whisper-small-myanmar"
MODEL_MYA_ID = "chuuhtetnaing/whisper-small-myanmar"
MODEL_THA_ID = "biodatlab/whisper-th-medium-combined"
NLP_MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MMS_MYA_TTS_ID = "facebook/mms-tts-mya"

_tts_lock = threading.Lock()
device = "cuda" if torch.cuda.is_available() else "cpu"


def _get_hf_model_path(repo_id: str) -> str:
    
    # ค้นหา snapshot directory ของโมเดลใน models_cache/huggingface เพื่อโหลดแบบ Offline โดยตรง
    # ช่วยป้องกันปัญหา offline alias resolution และ symlink เมื่อย้ายงานไปรันบนเครื่องใหม่
    folder_name = f"models--{repo_id.replace('/', '--')}"
    snapshots_dir = MODELS_DIR / "huggingface" / "hub" / folder_name / "snapshots"
    if snapshots_dir.exists():
        snapshots = [s for s in snapshots_dir.iterdir() if s.is_dir()]
        if snapshots:
            return str(snapshots[0])
    return repo_id


# --- Global Variables สำหรับเก็บ Model และ Tokenizer --------------------------
# Whisper small 
# SentenceTransformer NLP
stt_model = None         
nlp_model = None         

# whisper fintune สำหรับภาษาเมียนมา หากโหลดไม่สำเร็จจะ fallback ไปใช้ whisper medium
stt_mya_processor = None
stt_mya_model = None

# whisper fintune สำหรับภาษาไทย หากโหลดไม่สำเร็จจะ fallback ไปใช้ whisper medium
stt_tha_processor = None
stt_tha_model = None

# Text to Speech Models 
vits_mya_tokenizer = None
vits_mya_model = None
pythaitts_model = None
sherpa_zh_tts = None     

def get_device() -> str:
    return device

def load_models(log_cb=print) -> None:
    global stt_model, nlp_model, device, stt_mya_processor, stt_mya_model, stt_tha_processor, stt_tha_model

    # 1. Whisper small เป็นโมเดลหลัก 
    log_cb("กำลังโหลดโมเดล Whisper .....")
    whisper_cache_dir = str(MODELS_DIR / "whisper")
    try:
        stt_model = whisper.load_model("small", device=device, download_root=whisper_cache_dir)
    except Exception:
        torch.cuda.empty_cache()
        device = "cpu"
        stt_model = whisper.load_model("small", device=device, download_root=whisper_cache_dir)

    # whisper fintune สำหรับภาษาเมียนมา
    try:
        from transformers import WhisperProcessor, WhisperForConditionalGeneration

        model_path = _get_hf_model_path(MODEL_ID)
        stt_mya_processor = WhisperProcessor.from_pretrained(model_path, local_files_only=True)
        target_device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            stt_mya_model = WhisperForConditionalGeneration.from_pretrained(
                model_path, local_files_only=True
            ).to(target_device)
        except Exception:
            torch.cuda.empty_cache()
            target_device = "cpu"
            stt_mya_model = WhisperForConditionalGeneration.from_pretrained(
                model_path, local_files_only=True
            ).to(target_device)
        log_cb(f"โหลดโมเดล Whisper สำเร็จ ({target_device.upper()})")
    except Exception as e:
        stt_mya_processor = None
        stt_mya_model = None
        log_cb(f"ไม่สามารถโหลดโมเดล Whisper fintune ระบบสลับใช้ Whisper : {e}")

    # whisper fintune สำหรับภาษาไทย
    try:
        from transformers import WhisperProcessor, WhisperForConditionalGeneration

        model_path_tha = _get_hf_model_path(MODEL_THA_ID)
        stt_tha_processor = WhisperProcessor.from_pretrained(model_path_tha, local_files_only=True)
        target_device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            if target_device == "cpu":
                stt_tha_model = WhisperForConditionalGeneration.from_pretrained(
                    model_path_tha, local_files_only=True
                ).to(target_device, dtype=torch.float32)
            else:
                stt_tha_model = WhisperForConditionalGeneration.from_pretrained(
                    model_path_tha, local_files_only=True
                ).to(target_device)
        except Exception:
            torch.cuda.empty_cache()
            target_device = "cpu"
            stt_tha_model = WhisperForConditionalGeneration.from_pretrained(
                model_path_tha, local_files_only=True
            ).to(target_device, dtype=torch.float32)

        forced_ids_tha = stt_tha_processor.get_decoder_prompt_ids(language="th", task="transcribe")
        stt_tha_model.config.forced_decoder_ids = forced_ids_tha
        if hasattr(stt_tha_model, "generation_config") and stt_tha_model.generation_config is not None:
            stt_tha_model.generation_config.forced_decoder_ids = forced_ids_tha

        log_cb(f"โหลดโมเดล Whisper ภาษาไทยสำเร็จ ({target_device.upper()})")
    except Exception as e:
        stt_tha_processor = None
        stt_tha_model = None
        log_cb(f"ไม่สามารถโหลดโมเดล Whisper ภาษาไทย fintune ระบบสลับใช้ Whisper : {e}")

    # SentenceTransformer NLP สำหรับ embedding และ semantic search
    log_cb("กำลังโหลดโมเดล SentenceTransformer...")
    nlp_path = _get_hf_model_path(NLP_MODEL_ID)
    try:
        nlp_model = SentenceTransformer(nlp_path, device=device)
    except Exception:
        torch.cuda.empty_cache()
        device = "cpu"
        nlp_model = SentenceTransformer(nlp_path, device=device)
        log_cb("กำลังโหลดโมเดล SentenceTransformer...")


    # โหลดโมเดล Text to Speech 
    _load_tts_models(log_cb)


def transcribe_myanmar(wav_path: str) -> str:
    # ถอดเสียงภาษาพม่าโดยใช้โมเดล whisper fintune แทน Whisper small หากโมเดลนี้ไม่พร้อมใช้งาน จะ return เป็น string ว่าง
    if stt_mya_model is None or stt_mya_processor is None:
        return ""
    # ใช้ whisper.load_audio ที่มีอยู่แล้ว เรียก ffmpeg 
    # ไฟล์เสียงเป็น mono 16kHz float32 ให้ตรงกับ input ที่โมเดลนี้ต้องการ
    audio = whisper.audio.load_audio(wav_path)
    inputs = stt_mya_processor(audio, sampling_rate=16000, return_tensors="pt")
    input_features = inputs.input_features.to(stt_mya_model.device)

    with torch.no_grad():
        predicted_ids = stt_mya_model.generate(input_features)

    text = stt_mya_processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    return text.strip()


def transcribe_thai(wav_path: str) -> str:
    # ถอดเสียงภาษาไทยโดยใช้โมเดล whisper fintune (biodatlab/whisper-th-medium-combined)
    # หากโมเดลนี้ไม่พร้อมใช้งาน จะ return เป็น string ว่าง เพื่อ fallback ไปใช้ Whisper medium/small อัตโนมัติ
    if stt_tha_model is None or stt_tha_processor is None:
        return ""
    try:
        audio = whisper.audio.load_audio(wav_path)
        inputs = stt_tha_processor(audio, sampling_rate=16000, return_tensors="pt")
        input_features = inputs.input_features.to(stt_tha_model.device, dtype=stt_tha_model.dtype)

        forced_ids = stt_tha_processor.get_decoder_prompt_ids(language="th", task="transcribe")
        with torch.no_grad():
            predicted_ids = stt_tha_model.generate(input_features, forced_decoder_ids=forced_ids)

        text = stt_tha_processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        return text.strip()
    except Exception:
        return ""


WHISPER_LANG_MAP = {
    "th": "th",
    "chinese": "zh",
    "zh": "zh",
    "burmese": "my",
    "my": "my",
}


def transcribe_audio(wav_path: str, lang_code: str) -> str:
    
    # ถอดเสียงด้วย Speech to Text ตามภาษาที่เลือก
    # Burmese ให้ใช้ chuuhtetnaing/whisper-small-myanmar หากไม่สำเร็จ ให้ fallback ไปใช้ Whisper small
    # Thai ให้ใช้ biodatlab/whisper-th-medium-combined หากไม่สำเร็จ ให้ fallback ไปใช้ Whisper small
    # Chinese ให้ใช้ Whisper small
    text = ""
    if lang_code in ("burmese", "my"):
        text = transcribe_myanmar(wav_path)
    elif lang_code in ("th", "thai"):
        text = transcribe_thai(wav_path)

    if not text and stt_model is not None:
        whisper_lang = WHISPER_LANG_MAP.get(lang_code, lang_code)
        result = stt_model.transcribe(wav_path, language=whisper_lang, fp16=False)
        text = result.get("text", "").strip()

    return text

def _load_tts_models(log_cb=print) -> None:
    global vits_mya_tokenizer, vits_mya_model
    global pythaitts_model
    global sherpa_zh_tts

    from transformers import VitsModel, AutoTokenizer

    # ภาษาพม่า (facebook/mms-tts-mya)
    try:
        log_cb("กำลังโหลด Text to Speech ภาษาเมียนมา...")
        mya_tts_path = _get_hf_model_path(MMS_MYA_TTS_ID)
        vits_mya_tokenizer = AutoTokenizer.from_pretrained(mya_tts_path, local_files_only=True)
        vits_mya_model = VitsModel.from_pretrained(mya_tts_path, local_files_only=True).to(device)
        log_cb("โหลด Text to Speech ภาษาเมียนมาสำเร็จ")
    except Exception as e:
        log_cb(f"ไม่สามารถโหลด Text to Speech ภาษาเมียนมาได้: {e}")

    # ภาษาไทย (PyThaiTTS - vachana)
    try:
        log_cb("กำลังโหลด Text to Speech ภาษาไทย...")
        from pythaitts import TTS

        pythaitts_model = TTS(pretrained="vachana", device=device)
        log_cb("โหลด Text to Speech ภาษาไทยสำเร็จ")
    except Exception as e:
        pythaitts_model = None
        log_cb(f"ไม่สามารถโหลด Text to Speech ภาษาไทยได้: {e}")

    # ภาษาจีน (Sherpa-ONNX AISHELL-3)
    try:
        log_cb("กำลังโหลด Text to Speech ภาษาจีน...")
        import sherpa_onnx
        sherpa_dir = MODELS_DIR / "sherpa"
        vits_config = sherpa_onnx.OfflineTtsVitsModelConfig(
            model=str(sherpa_dir / "vits-aishell3.onnx"),
            lexicon=str(sherpa_dir / "lexicon.txt"),
            tokens=str(sherpa_dir / "tokens.txt"),
        )
        model_config = sherpa_onnx.OfflineTtsModelConfig(vits=vits_config, num_threads=1)
        config = sherpa_onnx.OfflineTtsConfig(model=model_config)
        sherpa_zh_tts = sherpa_onnx.OfflineTts(config)
        log_cb("โหลด Text to Speech ภาษาจีนสำเร็จ")
    except Exception as e:
        log_cb(f"ไม่สามารถโหลด Text to Speech ภาษาจีนได้: {e}")


def speak(text: str, tts_mode: str, log_cb=print) -> None:
    if not text.strip():
        return

    try:
        with _tts_lock:
            import sounddevice as sd

            # --- ภาษาไทย ------------------------------------------
            if tts_mode == "vits_tha":
                if pythaitts_model is None:
                    log_cb("โมเดล Text to Speech ภาษาไทยยังไม่พร้อมใช้งาน")
                    return

                import soundfile as sf
                temp_wav = str(TEMP_AUDIO_DIR / "tha_tts_output.wav")
                pythaitts_model.tts(text, speaker_idx="th_f_1", filename=temp_wav)

                data, samplerate = sf.read(temp_wav)
                sd.play(data, samplerate)
                sd.wait()

            # --- ภาษาจีน ------------------------------------------
            elif tts_mode == "sherpa_zh":
                if sherpa_zh_tts is None:
                    log_cb("โมเดล Text to Speech ภาษาจีนยังไม่พร้อมใช้งาน")
                    return

                audio = sherpa_zh_tts.generate(text, sid=0, speed=1.0)
                sd.play(audio.samples, audio.sample_rate)
                sd.wait()

            # --- ภาษาพม่า ------------------------------------------
            elif tts_mode == "vits_mya":
                if vits_mya_tokenizer is None or vits_mya_model is None:
                    log_cb("โมเดล Text to Speech ภาษาเมียนมายังไม่พร้อมใช้งาน")
                    return

                inputs = vits_mya_tokenizer(text, return_tensors="pt")
                inputs = {k: v.to(device) for k, v in inputs.items()}
                with torch.no_grad():
                    waveform = vits_mya_model(**inputs).waveform

                audio = waveform.squeeze().cpu().numpy()
                sr = getattr(vits_mya_model.config, "sampling_rate", 16000)
                sd.play(audio, samplerate=sr)
                sd.wait()

            else:
                log_cb(f"ไม่รู้จักโหมด Text to Speech: {tts_mode}")

    except Exception as e:
        log_cb(f"เกิดข้อผิดพลาดขณะแปลงข้อความเป็นเสียง ({tts_mode}): {e}")