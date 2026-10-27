import sys
import time
import threading
from pathlib import Path

import customtkinter as ctk
from PIL import Image
import speech_recognition as sr

import models  # load_models, speak
import chat    # load_intents, match_intent, get_fallback
import dictionary  # load_dictionary, correct_text
# ─── PATH SETUP ───────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
TEMP_AUDIO_DIR = ASSETS_DIR / "temp_audio"

# สร้างโฟลเดอร์เก็บไฟล์เสียงชั่วคราวอัตโนมัติหากยังไม่มี
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ─── CONFIG ───────────────────────────────────────────────────────────────────
LANG_CONFIG = {
    "ไทย":    {"code": "th",      "wav": str(TEMP_AUDIO_DIR / "thai.wav"),    "tts": "vits_tha",  "flag": str(ASSETS_DIR / "image" / "Thailand.png")},
    "中文":   {"code": "chinese", "wav": str(TEMP_AUDIO_DIR / "chinese.wav"), "tts": "sherpa_zh", "flag": str(ASSETS_DIR / "image" / "China.png")},
    "မြန်မာ": {"code": "burmese",      "wav": str(TEMP_AUDIO_DIR / "myanmar.wav"), "tts": "vits_mya",  "flag": str(ASSETS_DIR / "image" / "Myanmar.png")},
}

# ธีม "ขาว-น้ำเงิน" โมเดิร์น สะอาดตา อ่านง่าย
COLORS = {
    "bg":          "#F3F7FF",   # พื้นหลังหลัก ขาวอมฟ้าอ่อนมาก
    "surface":     "#FFFFFF",   # พื้นผิวการ์ด/หัวข้อ สีขาวล้วน
    "panel":       "#FFFFFF",   # แถบ header/แถบล่าง สีขาว
    "card":        "#EAF2FF",   # กล่องอินพุต/พื้นหลังภาษา ฟ้าอ่อน
    "accent":      "#1E12A2",   # น้ำเงินสดใส สำหรับปุ่ม/ไฮไลต์หลัก
    "accent_hover":"#255ECC",
    "accent2":     "#100078",   # น้ำเงินอ่อน สำหรับไฮไลต์รอง
    "bubble_bot":  "#EAF2FF",   # บับเบิลบอท ฟ้าอ่อน
    "bubble_usr":  "#2F6FED",   # บับเบิลผู้ใช้ น้ำเงินสด
    "text":        "#10233F",   # ข้อความหลัก กรมท่าเข้ม อ่านง่ายบนพื้นขาว
    "text_on_accent": "#FFFFFF",
    "muted":       "#02112E",   # ข้อความรอง เทาอมฟ้า
    "border":      "#DCE6F7",   # เส้นขอบอ่อนๆ
    "success":     "#16A34A",
    "success_hover":"#128A3E",
    "warn":        "#DF4A00",
    "danger":      "#900808",
    "danger_hover":"#660101",
    "mic_idle":    "#AA0303",   # แดง = ปุ่มไมค์สถานะปกติ
    "mic_active":  "#16A34A",   # เขียว = ปุ่มไมค์ตอนกำลังฟัง
}

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


# ---- คลาสเเชทบอท gui ------------------------------------------------
class ChatbotGUI:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("ระบบผู้ช่วยโต้ตอบด้วยเสียงสำหรับให้คำปรึกษาด้านความเครียดเบื้องต้น ")
        # เปิดเต็มหน้าจอ คลุมทั้งจอ 100% ไม่มีขอบหน้าต่างและไม่มีปุ่มกดปิด (Fullscreen Borderless / Kiosk Mode)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_w}x{screen_h}+0+0")
        self.root.attributes("-fullscreen", True)
        self.root.state("zoomed")
        self.root.after(100, lambda: self.root.attributes("-fullscreen", True))

        self.root.bind_all("<Control-d>", self._on_exit)
        self.root.bind_all("<Control-D>", self._on_exit)
        self.root.bind_all("<Control-Key-d>", self._on_exit)
        self.root.bind_all("<Control-Key-D>", self._on_exit)
        self.root.bind_all("<Escape>", self._on_exit)

        ico_path = ASSETS_DIR / "image" / "app_icon.ico"
        if ico_path.exists():
            try:
                self.root.iconbitmap(str(ico_path))
            except Exception:
                pass
        self.root.configure(fg_color=COLORS["bg"]) #ระบุสสีพพื้นหลัง
        self.selected_lang = ctk.StringVar(value="ไทย")
        self.is_listening  = False   # ใช้ปรับสีและข้อความปุ่มไมค์เท่านั้น
        self._recording_active = False  # true ตลอดช่วงที่ thread บันทึกเสียงกำลังทำงานจริง
        self.models_ready  = False
        self._session_id = 0
        self._build_ui()
        threading.Thread(target=self._init_models, daemon=True).start()

    def _on_exit(self, event=None) -> None:
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    # --- สร้าง UI ทั้งหมด --------------------------------
    def _build_ui(self) -> None:
        self._build_header()
        self._build_lang_bar()
        self._build_chat_area()
        self._build_bottom_bar()

    def _build_header(self) -> None:
        hdr = ctk.CTkFrame(self.root, fg_color=COLORS["surface"], height=106, corner_radius=0, border_width=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # เส้นคั่นบางๆ ด้านล่าง header ให้ดูมีมิติแบบการ์ดโมเดิร์น
        divider = ctk.CTkFrame(hdr, fg_color=COLORS["border"], height=1)
        divider.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")

        #โหลดรูปภาพ กำหนดขนาด 68 x 68 px
        self.logo_img = None
        logo_path = ASSETS_DIR / "image" / "logo.png"
        try:
            pil_logo = Image.open(logo_path)
            self.logo_img = ctk.CTkImage(light_image=pil_logo, size=(86, 86)) # <-- ขนาด logo
        except Exception:
            print("ไม่สามารถทำการโหลดรูปภาพได้")
            self.logo_img = None

        # แสดง logo ระบุกำหนดชิดขอบซ้าย
        if self.logo_img:
            logo_label = ctk.CTkLabel(hdr, text="", image=self.logo_img, fg_color="transparent")
            logo_label.pack(side="left", padx=(20, 12), pady=10) # <-- ปรับระยห่างของ logo 

        # แสดงข้อความ hearder 
        title_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        title_frame.pack(side="left", fill="y", pady=10)

        t1 = ctk.CTkLabel(
            title_frame,
            text="สถานพินิจและคุ้มครองเด็กและเยาวชนจังหวัดตาก",
            fg_color="transparent", # <-- พื้นหลังโปร่งใส
            text_color=COLORS["text"],
            font=("Segoe UI", 26, "bold"),
            anchor="w"
        )
        t1.pack(fill="x", pady=(0, 0.3)) # <-- ปรับระยะห่างระหว่างบรรทัด

        t2 = ctk.CTkLabel(
            title_frame,
            text="กรมพินิจและคุ้มครองเด็กและเยาวชน",
            fg_color="transparent",
            text_color=COLORS["text"],
            font=("Segoe UI", 18, "bold"),
            anchor="w"
        )
        t2.pack(fill="x", pady=(0, 0.3)) # <-- ปรับระยะห่างระหว่างบรรทัด

        t3 = ctk.CTkLabel(
            title_frame,
            text="Department of Juvenile Observation and Protection",
            fg_color="transparent",
            text_color=COLORS["text"],  
            font=("Segoe UI", 14),
            anchor="w"
        )
        t3.pack(fill="x", pady=(0, 0.3)) # <-- ปรับระยะห่างระหว่างบรรทัด

        # แสดงสถานะการทำงานของระบบ
        self.status_dot = ctk.CTkLabel(hdr, text="⬤ กำลังโหลด...", fg_color="transparent", text_color=COLORS["warn"], font=("Segoe UI", 24, "bold"), corner_radius=7, width=125, height=38)
        self.status_dot.place(relx=1.0, rely=0.5, anchor="e", x=-180) # <-- ปรับระยะห่างจากขอบขวา

        self.clear_btn = ctk.CTkButton(hdr, text="🗘 รีเซ็ต", fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"], text_color="white", font=("Segoe UI", 20, "bold"), corner_radius=7, width=125, height=38, command=self._clear_chat)
        self.clear_btn.place(relx=1.0, rely=0.5, anchor="e", x=-20)


    # ------ เลือกภาษา ------------------------------
    def _build_lang_bar(self) -> None:
        lang_bar = ctk.CTkFrame(self.root, fg_color=COLORS["surface"], height=126, corner_radius=0)
        lang_bar.pack(fill="x")

        center_frame = ctk.CTkFrame(lang_bar, fg_color="transparent")
        center_frame.pack(expand=True, pady=12)

        #ctk.CTkLabel(center_frame, text="เลือกภาษา:",fg_color="transparent", text_color=COLORS["muted"],font=("Segoe UI", 15, "bold")).grid(row=0, column=0, padx=(0, 15), sticky="w")
        self.lang_btns = {}
        self.flag_images = {}

        for i, (lang, cfg) in enumerate(LANG_CONFIG.items(), start=0):
            try:
                pil_flag = Image.open(cfg["flag"])
                self.flag_images[lang] = ctk.CTkImage(light_image=pil_flag, size=(98, 54)) # <-- ขนาดธงชาติ
            except Exception as e:
                print(f"ไม่สามารถโหลดรูปธงชาติ {lang} ได้: {e}")
                self.flag_images[lang] = None

            btn = ctk.CTkButton(center_frame,text=lang,image=self.flag_images[lang],compound="top",width=136, height=126,corner_radius=14,fg_color=COLORS["surface"],text_color=COLORS["muted"],hover_color=COLORS["border"],font=("Segoe UI", 16, "bold"),command=lambda l=lang: self._select_lang(l))
            btn.grid(row=0, column=i, padx=12)
            self.lang_btns[lang] = btn
        self._select_lang("ไทย")  # <-- ภาษาเริ่มต้น


    # ---- พื้นที่เเสดงข้อความสนทนา ------------------------------
    def _build_chat_area(self) -> None:
        chat_frame = ctk.CTkFrame(self.root, fg_color=COLORS["bg"], corner_radius=0)
        chat_frame.pack(fill="both", expand=True, padx=0, pady=(0, 0))

        self.chat_scroll = ctk.CTkScrollableFrame(chat_frame, fg_color=COLORS["surface"], corner_radius=8,border_width=4, border_color=COLORS["border"],scrollbar_button_color=COLORS["accent2"],scrollbar_button_hover_color=COLORS["accent"])
        self.chat_scroll.pack(fill="both", expand=True)
        self.chat_scroll.grid_columnconfigure(0, weight=1)

        # ขนาดฟอนต์ข้อความสนทนา
        self.chat_font_size = 24
        self._msg_row_index = 0

    def _build_bottom_bar(self) -> None:
        bottom = ctk.CTkFrame(self.root, fg_color=COLORS["surface"], height=180, corner_radius=0)
        bottom.pack(fill="x", side="bottom")
        bottom.pack_propagate(False)

        divider = ctk.CTkFrame(bottom, fg_color=COLORS["border"], height=1)
        divider.place(relx=0, rely=0, relwidth=1.0, anchor="nw")

        # microphone button (ขนาดวงกลม 1:1 สมส่วน คมชัด และขนาดใหญ่ขึ้น)
        self.mic_width = 135
        self.mic_height = 135

        # โหลดรูปภาพปุ่มไมค์ (idle = สถานะปกติ, active = กำลังฟัง)
        self.mic_idle_img = None
        self.mic_active_img = None
        mic_idle_path = ASSETS_DIR / "image" / "mic_idle.png"
        if not mic_idle_path.exists():
            mic_idle_path = ASSETS_DIR / "image" / "mic_idle.png.png"
        mic_active_path = ASSETS_DIR / "image" / "mic_active.png"
        if not mic_active_path.exists():
            mic_active_path = ASSETS_DIR / "image" / "mic_active.png.png"

        try:
            pil_idle = Image.open(mic_idle_path)
            # ตัดพื้นที่ว่างใสรอบๆ ออก ให้เหลือเฉพาะตัวไอคอนวงกลมไมค์ 1:1 สมส่วน
            bbox = pil_idle.getbbox()
            if bbox:
                pil_idle = pil_idle.crop(bbox)
            self.mic_idle_img = ctk.CTkImage(light_image=pil_idle, size=(self.mic_width, self.mic_height))
        except Exception as e:
            print(f"ไม่สามารถโหลดรูป mic_idle ได้: {e}")

        try:
            pil_active = Image.open(mic_active_path)
            bbox = pil_active.getbbox()
            if bbox:
                pil_active = pil_active.crop(bbox)
            self.mic_active_img = ctk.CTkImage(light_image=pil_active, size=(self.mic_width, self.mic_height))
        except Exception as e:
            print(f"ไม่สามารถโหลดรูป mic_active ได้: {e}")

        # ถ้ามีรูปภาพ ให้แสดงเฉพาะรูปภาพบนพื้นหลังโปร่งใสตามหลักการ logo_img
        if self.mic_idle_img:
            self.mic_btn = ctk.CTkLabel(
                bottom,
                text="",
                image=self.mic_idle_img,
                fg_color="transparent",
                cursor="hand2",
            )
        else:
            self.mic_btn = ctk.CTkButton(
                bottom,
                text="      🎙️ \nกดค้างพูด",
                width=self.mic_width,
                height=self.mic_height,
                corner_radius=8,
                fg_color=COLORS["mic_idle"],
                hover_color=COLORS["mic_idle"],
                text_color="white",
                font=("Segoe UI", 26, "bold"),
            )
        self.mic_btn.pack(pady=(20, 0))
        self.mic_btn.bind("<ButtonPress-1>", self._mic_press)
        self.mic_btn.bind("<ButtonRelease-1>", self._mic_release)

        # ── แถวช่องพิมพ์ข้อความ ──
        # input_frame = ctk.CTkFrame(bottom, fg_color=COLORS["card"], corner_radius=14)
        # input_frame.pack(fill="x", padx=16, pady=(14, 16))
        # self.text_input = ctk.CTkEntry(input_frame, fg_color="transparent", text_color=COLORS["text"],border_width=0, font=("Segoe UI", 16),placeholder_text="พิมพ์ข้อความ")
        # self.text_input.pack(side="left", fill="x", expand=True, ipady=10, padx=12, pady=6)
        # self.text_input.bind("<Return>", lambda e: self._send_text())
        # # chatbar 
        # ctk.CTkButton(input_frame, text="ส่งข้อความ",fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],text_color="white", font=("Segoe UI", 15, "bold"),corner_radius=10, width=100, height=44,command=self._send_text).pack(side="right", padx=8, pady=6)


    # ---- เงื่อนไขการเลือกภาษา -------------------------------
    def _select_lang(self, lang: str) -> None:
        self.selected_lang.set(lang)
        for l, btn in self.lang_btns.items():
            if l == lang:
                btn.configure(fg_color=COLORS["accent"], text_color="white",border_color=COLORS["accent"], font=("Segoe UI", 16, "bold"))
            else:
                btn.configure(fg_color=COLORS["surface"], text_color=COLORS["muted"],border_color=COLORS["border"], font=("Segoe UI", 16, "bold"))


    # --- โหลดโมเดลเเละฐานข้อมูลเบื้องหลังเเละส่งสถานะการทำงาน -------------------------------
    def _init_models(self) -> None:
        self.root.after(0, self._set_controls_enabled, False)
        try:
            models.load_models(self._append_sys)
            chat.load_intents(self._append_sys)
            dictionary.load_dictionary()
            self.models_ready = True
            self.root.after(0, lambda: self.status_dot.configure(text="⬤ พร้อม", text_color=COLORS["success"]))
            self.root.after(0, self._set_controls_enabled, True)
        except Exception as e:
            self.models_ready = False
            self.root.after(0, lambda: self.status_dot.configure(text="⬤ โหลดโมเดลล้มเหลว", text_color=COLORS["danger"]))
            self.root.after(0, lambda err=e: self._append_sys(f"โหลดโมเดลไม่สำเร็จกรุณาปิดโปรแกรมแล้วเปิดใหม่หรือติดต่อผู้ดูแลระบบ: {err}"))

    def _set_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        # หากใช้ปุ่มแบบภาพ (CTkLabel) จะไม่สั่ง state="disabled" เพื่อไม่ให้ Tkinter ทำลายจุดตาข่ายสีเทา
        # ระบบมี if not self.models_ready: return ดักการกดไว้ให้อยู่แล้วอย่างปลอดภัย
        if isinstance(self.mic_btn, ctk.CTkButton):
            self.mic_btn.configure(state=state)
        # self.text_input.configure(state=state)


    # ---- การเเสดงการสนทนา -------------------------------
    def _append_sys(self, msg: str) -> None:
        self.root.after(0, lambda m=msg: self._write_sys(m))

    def _write_sys(self, msg: str) -> None:
        row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        row.pack(fill="x", pady=(2, 2))
        ctk.CTkLabel(row, text=msg, fg_color="transparent",text_color=COLORS["warn"],font=("Segoe UI", 16)).pack(anchor="w", padx=12)  # <-- แสดงสถานะการทำงานเเละโหลดโมเดล
        self._scroll_to_bottom()

    def _append_message(self, speaker: str, text: str, score: float | None = None,tag: str | None = None) -> None:
        try:
            self._append_message_impl(speaker, text, score, tag)
        except Exception as e:
            self._write_sys(f"ไม่สามารถแสดงข้อความบนจอได้: {e}")

    def _append_message_impl(self, speaker: str, text: str, score: float | None = None, tag: str | None = None) -> None:
        ts = time.strftime("%H:%M")
        row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        row.pack(fill="x", pady=8, padx=6)

        # -- ข้อความจากผู้ใช้ --------------------------------
        if speaker == "user":
            container = ctk.CTkFrame(row, fg_color="transparent")
            container.pack(anchor="e")
            ctk.CTkLabel(container, text=f"คุณ  ·  {ts}",fg_color="transparent", text_color=COLORS["accent"],font=("Segoe UI", 16, "bold")).pack(anchor="e")

            # กล่องข้อความผู้ใช้
            bubble = ctk.CTkLabel(container, text=text, justify="left", wraplength=880,fg_color=COLORS["bubble_usr"], text_color=COLORS["text_on_accent"],corner_radius=8, font=("Segoe UI", self.chat_font_size)) # <-- ระบุขนาดข้อความบรรทัดที่ 180
            bubble.pack(anchor="e", ipadx=8, ipady=16)

        # --- ข้อความจากบอท --------------------------------
        else:
            container = ctk.CTkFrame(row, fg_color="transparent")
            container.pack(anchor="w")

            meta = f"บอท  ·  {ts}"
            if score is not None:
                meta += f"   (score: {score:.2f})"
            ctk.CTkLabel(container, text=meta,fg_color="transparent", text_color=COLORS["accent2"],font=("Segoe UI", 16, "bold")).pack(anchor="w")

            if tag:
                ctk.CTkLabel(container, text=f"predicted tag: {tag}",fg_color="transparent", text_color=COLORS["muted"],font=("Segoe UI", 16)).pack(anchor="w")
            
            # กล่องข้อความจากบอท
            bubble = ctk.CTkLabel(container, text=text, justify="left", wraplength=880,fg_color=COLORS["bubble_bot"], text_color=COLORS["text"],corner_radius=8, font=("Segoe UI", self.chat_font_size)) # <-- ระบุขนาดข้อความบรรทัดที่ 180
            bubble.pack(anchor="w", ipadx=8, ipady=16, pady=(2, 6))

            replay_btn = ctk.CTkButton(
                container, text="🔊 ฟังอีกครั้ง",
                fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
                text_color="white", font=("Segoe UI", 16, "bold"),
                corner_radius=8, width=126, height=34,
                command=lambda t=text: self._replay_voice(t))
            replay_btn.pack(anchor="w")

        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        def _do_scroll():
            self.chat_scroll.update_idletasks()
            self.chat_scroll._parent_canvas.yview_moveto(1.0)
        self.root.after(20, _do_scroll)


    # --- การส่งข้อความ -------------------------------
    def _send_text(self) -> None:
        txt = self.text_input.get().strip()
        if not txt:
            return
        self.text_input.delete(0, "end")
        cfg = LANG_CONFIG[self.selected_lang.get()]

        # Data Dictionary 
        corrected = dictionary.correct_text(txt, cfg["code"])
        self._process_input(corrected, raw_text=txt)


    # --- ล้างประวัติการสนทนา -------------------------------
    def _clear_chat(self) -> None:
        self._session_id += 1
        for widget in self.chat_scroll.winfo_children():
            widget.destroy()
        self._append_sys("ล้างประวัติการแชทเรียบร้อยแล้ว")


    # --- เล่นเสียงอีกครั้ง -------------------------------
    def _replay_voice(self, text: str) -> None:
        if not self.models_ready:
            return
        cfg = LANG_CONFIG[self.selected_lang.get()]
        threading.Thread(target=models.speak, args=(text, cfg["tts"], self._append_sys), daemon=True).start()


    # --- ไมโครโฟนเเละการรับเสียง -------------------------------
    def _mic_press(self, event) -> None:
        if not self.models_ready:
            return
        if self._recording_active:
            return
        self._recording_active = True
        self.is_listening = True
        if self.mic_active_img:
            self.mic_btn.configure(image=self.mic_active_img)
        else:
            self.mic_btn.configure(fg_color=COLORS["mic_active"], hover_color=COLORS["mic_active"], text="      🎙️ \nระบบกำลังฟัง")
        threading.Thread(target=self._listen_thread, daemon=True).start()

    def _mic_release(self, event) -> None:
        self.is_listening = False
        if self.mic_idle_img:
            self.mic_btn.configure(image=self.mic_idle_img)
        else:
            self.mic_btn.configure(fg_color=COLORS["mic_idle"], hover_color=COLORS["mic_idle"], text="      🎙️ \nกดค้างเพื่อพูด")


    # --- การฟังเสียงพูดเเละการถอดเสียงด้วย whisper ---------------------------------------
    def _listen_thread(self) -> None:
        lang      = self.selected_lang.get()
        cfg       = LANG_CONFIG[lang]
        wav_out   = cfg["wav"]
        lang_code = cfg["code"]

        rec = sr.Recognizer()

        rec.dynamic_energy_threshold = False
        rec.energy_threshold = 300 # <-- ปรับค่าสูจะไม่ได้รับเสียงรบกวน
        rec.pause_threshold = 2.0 # <-- หยุดพูดกี่วิถึงตัดจบ
        rec.non_speaking_duration = 0.8  # <-- ช่วงเวลาสำรองเสียงเงียบเพื่อไม่ให้คำพูดถูกตัดขอบ

        try:
            try:
                with sr.Microphone() as source:
                    rec.adjust_for_ambient_noise(source, duration=0.1)
                    self._append_sys("ดำเนินการถอดเสียง")
                    audio = rec.listen(source, timeout=10, phrase_time_limit=15)
            except OSError as e:
                self._append_sys(f"ไม่พบไมโครโฟนกรุณาตรวจสอบการเชื่อมต่ออุปกรณ์: {e}")
                return

            with open(wav_out, "wb") as f:
                f.write(audio.get_wav_data())

            # 1. ถอดเสียงตามภาษาที่เลือกด้วย Whisper 
            raw_text = models.transcribe_audio(wav_out, lang_code)

            if raw_text:
                # 2. นำข้อความจาก Whisper เข้าสู่ Data Dictionary เพื่อแก้ไขคำผิด
                corrected_text = dictionary.correct_text(raw_text, lang_code)
                self.root.after(0, lambda r=raw_text, c=corrected_text: self._process_input(c, raw_text=r))
            else:
                self._append_sys("ไม่ได้ยินเสียงพูดที่ชัดเจนกรุณาลองพูดใหม่อีกครั้งครับ")

        except sr.WaitTimeoutError:
            self._append_sys("หมดเวลารอไม่ได้ยินเสียงพูดกรุณาลองใหม่อีกครั้ง")
        except Exception as e:
            self._append_sys(f"เกิดข้อผิดพลาดขณะประมวลผลเสียง: {e}")
        finally:
            self._recording_active = False

            def _reset_mic():
                if self.mic_idle_img:
                    self.mic_btn.configure(image=self.mic_idle_img)
                else:
                    self.mic_btn.configure(
                        fg_color=COLORS["mic_idle"],
                        hover_color=COLORS["mic_idle"],
                        text="      🎙️ \nกดค้างเพื่อพูด",
                    )
                self.is_listening = False

            self.root.after(0, _reset_mic)

    # --- จัดการข้อความผู้ใช้และส่งประมวลผลคำตอบ -------------------------------
    def _process_input(self, text: str, raw_text: str | None = None) -> None:
        if not self.models_ready:
            self._append_sys("โมเดลยังไม่พร้อมกรุณารอโหลดโมเดลให้เสร็จสิ้นก่อนใช้งาน")
            return
        cfg = LANG_CONFIG[self.selected_lang.get()]
        sid = self._session_id
        actual_raw = raw_text if raw_text is not None else text
        self._append_message("user", text)
        threading.Thread(target=self._reply_thread,args=(text, cfg, sid, actual_raw), daemon=True).start()

    def _reply_thread(self, text: str, cfg: dict, sid: int, raw_text: str = "") -> None:
        try:
            resp, score, tag, best_pattern = chat.match_intent(cfg["code"], text)

            # Debug Log แสดงผลการทำงานของ Pipeline อย่างละเอียด
            print("Whisper Text:")
            print(raw_text or text)
            print("\nCorrected Text:")
            print(text)
            print("\nBest Pattern:")
            print(best_pattern or "-")
            print(f"\nSimilarity:\n{score:.2f}")
            print(f"\nTag:\n{tag or '-'}")

            if sid != self._session_id:
                return

            if resp:
                self.root.after(0, lambda: self._append_message("bot", resp, score, tag))
                threading.Thread(target=models.speak,args=(resp, cfg["tts"], self._append_sys), daemon=True).start()
            else:
                fb = chat.get_fallback(cfg["tts"])
                display = fb if fb else "(ไม่เข้าใจ)"
                self.root.after(0, lambda: self._append_message("bot", display, score))
                if fb:
                    threading.Thread(target=models.speak,args=(fb, cfg["tts"], self._append_sys), daemon=True).start()
        except Exception as e:
            if sid == self._session_id:
                self.root.after(0, lambda err=e: self._append_sys(f"เกิดข้อผิดพลาดขณะประมวลผลคำตอบ: {err}"))
