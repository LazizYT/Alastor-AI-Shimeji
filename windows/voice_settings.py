import os
import json
import tkinter as tk
from tkinter import ttk, messagebox

from core.logger import log_info
from voice.radio_dsp import DSP_PROFILES
from voice.tts_engine import VOICE_PRESETS, DEFAULT_SETTINGS

VOICES_LIST = [
    ("ru-RU-DmitryNeural", "🇷🇺 Дмитрий (Русский мужской, канон Аластора)"),
    ("en-US-AndrewMultilingualNeural", "🌐 Эндрю (Русский/Мультиязычный, энергичный мужской)"),
    ("en-US-BrianMultilingualNeural", "🌐 Брайан (Русский/Мультиязычный, глубокий солидный бас)"),
    ("de-DE-FlorianMultilingualNeural", "🌐 Флориан (Русский/Мультиязычный, мягкий бархатистый)"),
    ("fr-FR-RemyMultilingualNeural", "🌐 Реми (Русский/Мультиязычный, харизматичный артистичный)"),
    ("en-AU-WilliamMultilingualNeural", "🌐 Уильям (Русский/Мультиязычный, уверенный мужской)"),
    ("uk-UA-OstapNeural", "🇺🇦 Остап (Славянский мужской тембр)"),
    ("en-US-GuyNeural", "🇺🇸 Guy (Английский оригинальный голос Аластора)"),
    ("en-US-ChristopherNeural", "🇺🇸 Christopher (Глубокий американский мужской)"),
    ("ru-RU-SvetlanaNeural", "🇷🇺 Светлана (Русский женский тембр)"),
]

FILTERS_LIST = [
    # 📻 Радиофильтры и винтаж
    ("canon_radio", "📻 Каноничный Аластор (Радио 1930-х)"),
    ("gramophone", "📻 Старый патефон / Граммофон (1920-е)"),
    ("am_radio", "📻 Коротковолновый эфир (Шумный AM-приёмник)"),
    ("walkie_talkie", "📻 Армейская рация Walkie-Talkie (Резкий эфир)"),
    ("telephone", "📞 Винтажная телефонная линия (1960-е)"),
    ("megaphone", "📢 Уличный рупор / Мегафон (Перегруз)"),
    ("demon_radio", "😈 Демонический эфир Аластора (Dark Overlord)"),
    ("shadow_realm", "🏛️ Театр теней / Эхо Преисподней"),
    # 🎙️ Обычные и студийные фильтры
    ("studio_warm", "🎙️ Тёплый студийный микрофон (Подкаст, мягкий бас)"),
    ("studio_crystal", "🎙️ Кристальная студия (High-End Clarity)"),
    ("studio_latenight", "🎙️ Ночной радиоведущий (Глубокий бархат)"),
    ("clean", "🎙️ Чистый звук (Bypass / Без эффектов и шумов)"),
]

class VoiceSettingsWindow:
    """
    Catppuccin-styled settings window for Alastor's voice,
    allowing real-time parameter tweaking, live preview, DSP customization, and presets.
    """
    def __init__(self, parent_root, tts_engine):
        self.parent = parent_root
        self.tts = tts_engine

        self.win = tk.Toplevel(self.parent)
        self.win.title("🎙️ Настройки голоса и радиовещания — Аластор")
        self.win.geometry("560x700")
        self.win.minsize(520, 640)
        self.win.configure(bg="#11111b")
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.97)

        # Style TTK widgets
        self._setup_styles()

        # Load active settings
        self.current_settings = self.tts.get_current_settings()

        # Tkinter Variables
        self.voice_var = tk.StringVar(value=self.current_settings.get("voice", "ru-RU-DmitryNeural"))
        self.filter_var = tk.StringVar(value=self.current_settings.get("filter_profile", "canon_radio"))
        
        # Parse rate integer from "+8%" or "-5%"
        rate_str = self.current_settings.get("rate", "+8%")
        rate_int = int(rate_str.replace("%", "").replace("+", "") or 0)
        self.rate_var = tk.IntVar(value=rate_int)

        # Parse pitch integer from "+2Hz" or "-10Hz"
        pitch_str = self.current_settings.get("pitch", "+2Hz")
        pitch_int = int(pitch_str.replace("Hz", "").replace("+", "") or 0)
        self.pitch_var = tk.IntVar(value=pitch_int)

        self.enabled_var = tk.BooleanVar(value=self.current_settings.get("enabled", True))
        self.dsp_var = tk.BooleanVar(value=self.current_settings.get("dsp_enabled", True))
        self.demon_layer_var = tk.BooleanVar(value=self.current_settings.get("demon_layer", True))
        self.vinyl_var = tk.BooleanVar(value=self.current_settings.get("add_vinyl", True))
        self.vinyl_int_var = tk.DoubleVar(value=float(self.current_settings.get("vinyl_intensity", 1.0)))
        
        self.highpass_var = tk.IntVar(value=int(self.current_settings.get("highpass_hz", 350)))
        self.lowpass_var = tk.IntVar(value=int(self.current_settings.get("lowpass_hz", 3800)))
        self.drive_var = tk.DoubleVar(value=float(self.current_settings.get("drive_db", 6.0)))

        self.preset_var = tk.StringVar(value="Кастомный профиль")
        self.status_var = tk.StringVar(value="Готов к эфиру")

        self._build_ui()
        self._detect_active_preset()

    def _setup_styles(self):
        style = ttk.Style(self.win)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        style.configure("Dark.TCombobox",
                        fieldbackground="#181825",
                        background="#313244",
                        foreground="#cdd6f4",
                        darkcolor="#181825",
                        lightcolor="#181825",
                        arrowcolor="#cba6f7",
                        bordercolor="#313244")
        self.win.option_add("*TCombobox*Listbox.background", "#181825")
        self.win.option_add("*TCombobox*Listbox.foreground", "#cdd6f4")
        self.win.option_add("*TCombobox*Listbox.selectBackground", "#45475a")
        self.win.option_add("*TCombobox*Listbox.selectForeground", "#cba6f7")

    def _build_ui(self):
        # Header
        header = tk.Frame(self.win, bg="#181825", pady=10, padx=16)
        header.pack(fill=tk.X)

        tk.Label(
            header, text="🎙️ Радио-транслятор: Настройки голоса Аластора",
            font=("Segoe UI", 11, "bold"), fg="#cba6f7", bg="#181825"
        ).pack(side=tk.LEFT)

        chk_master = tk.Checkbutton(
            header, text="Голос ВКЛ", variable=self.enabled_var,
            bg="#181825", fg="#a6e3a1", selectcolor="#11111b",
            activebackground="#181825", activeforeground="#a6e3a1",
            font=("Segoe UI", 9, "bold")
        )
        chk_master.pack(side=tk.RIGHT)

        # Scrollable container
        canvas = tk.Canvas(self.win, bg="#11111b", bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.win, orient="vertical", command=canvas.yview, bg="#181825")
        self.content_frame = tk.Frame(canvas, bg="#11111b", padx=16, pady=10)

        self.content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.content_frame, anchor="nw", width=520)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))

        # Section 1: Presets
        self._build_presets_section(self.content_frame)

        # Section 2: Neural Voice & Pitch/Rate
        self._build_speech_section(self.content_frame)

        # Section 3: Audio Filters (Radio & Normal)
        self._build_filter_section(self.content_frame)

        # Section 4: Live Audio Test Box
        self._build_test_section(self.content_frame)

        # Bottom Action Bar
        self._build_actions_bar()

    def _build_presets_section(self, parent):
        box = tk.LabelFrame(
            parent, text=" 📻 Готовые пресеты (Быстрый выбор) ",
            bg="#181825", fg="#89b4fa", font=("Segoe UI", 9, "bold"),
            padx=12, pady=10, bd=1, relief=tk.SOLID
        )
        box.pack(fill=tk.X, pady=(0, 10))

        preset_titles = [p["title"] for p in VOICE_PRESETS.values()]
        self.preset_combo = ttk.Combobox(
            box, values=preset_titles, textvariable=self.preset_var,
            state="readonly", style="Dark.TCombobox", font=("Segoe UI", 9)
        )
        self.preset_combo.pack(fill=tk.X, pady=4)
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)

    def _build_speech_section(self, parent):
        box = tk.LabelFrame(
            parent, text=" 🗣️ Голос (Русские и мужские модели) ",
            bg="#181825", fg="#89b4fa", font=("Segoe UI", 9, "bold"),
            padx=12, pady=10, bd=1, relief=tk.SOLID
        )
        box.pack(fill=tk.X, pady=(0, 10))

        # Voice dropdown
        tk.Label(box, text="Выберите голос диктора:", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).pack(anchor="w")
        voice_labels = [label for _, label in VOICES_LIST]
        self.voice_combo = ttk.Combobox(
            box, values=voice_labels, state="readonly", style="Dark.TCombobox", font=("Segoe UI", 9)
        )
        for code, label in VOICES_LIST:
            if code == self.voice_var.get():
                self.voice_combo.set(label)
                break
        self.voice_combo.pack(fill=tk.X, pady=(2, 8))
        self.voice_combo.bind("<<ComboboxSelected>>", self._on_voice_selected)

        # Speed / Rate Slider
        rate_frame = tk.Frame(box, bg="#181825")
        rate_frame.pack(fill=tk.X, pady=2)
        tk.Label(rate_frame, text="Скорость речи (Rate):", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.rate_val_lbl = tk.Label(rate_frame, text=f"{self.rate_var.get():+d}%", bg="#181825", fg="#cba6f7", font=("Segoe UI", 9, "bold"))
        self.rate_val_lbl.pack(side=tk.RIGHT)

        rate_slider = tk.Scale(
            box, from_=-40, to=40, orient=tk.HORIZONTAL, variable=self.rate_var,
            bg="#181825", fg="#cdd6f4", troughcolor="#313244", highlightthickness=0, bd=0,
            showvalue=False, command=lambda v: self.rate_val_lbl.config(text=f"{int(v):+d}%")
        )
        rate_slider.pack(fill=tk.X, pady=(0, 8))

        # Pitch Slider
        pitch_frame = tk.Frame(box, bg="#181825")
        pitch_frame.pack(fill=tk.X, pady=2)
        tk.Label(pitch_frame, text="Высота тона (Pitch):", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.pitch_val_lbl = tk.Label(pitch_frame, text=f"{self.pitch_var.get():+d}Hz", bg="#181825", fg="#cba6f7", font=("Segoe UI", 9, "bold"))
        self.pitch_val_lbl.pack(side=tk.RIGHT)

        pitch_slider = tk.Scale(
            box, from_=-30, to=30, orient=tk.HORIZONTAL, variable=self.pitch_var,
            bg="#181825", fg="#cdd6f4", troughcolor="#313244", highlightthickness=0, bd=0,
            showvalue=False, command=lambda v: self.pitch_val_lbl.config(text=f"{int(v):+d}Hz")
        )
        pitch_slider.pack(fill=tk.X, pady=(0, 4))

    def _build_filter_section(self, parent):
        box = tk.LabelFrame(
            parent, text=" 🎛️ Звуковые фильтры (Радио и обычные) ",
            bg="#181825", fg="#89b4fa", font=("Segoe UI", 9, "bold"),
            padx=12, pady=10, bd=1, relief=tk.SOLID
        )
        box.pack(fill=tk.X, pady=(0, 10))

        # Filter profile selector
        tk.Label(box, text="Выберите звуковой фильтр / окружение:", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).pack(anchor="w")
        filter_labels = [label for _, label in FILTERS_LIST]
        self.filter_combo = ttk.Combobox(
            box, values=filter_labels, state="readonly", style="Dark.TCombobox", font=("Segoe UI", 9)
        )
        for code, label in FILTERS_LIST:
            if code == self.filter_var.get():
                self.filter_combo.set(label)
                break
        self.filter_combo.pack(fill=tk.X, pady=(2, 10))
        self.filter_combo.bind("<<ComboboxSelected>>", self._on_filter_selected)

        # Radio DSP master switch
        chk_dsp = tk.Checkbutton(
            box, text="Включить обработку фильтрами (DSP активен)",
            variable=self.dsp_var, bg="#181825", fg="#cdd6f4", selectcolor="#11111b",
            activebackground="#181825", activeforeground="#cba6f7", font=("Segoe UI", 9)
        )
        chk_dsp.pack(anchor="w", pady=(0, 4))

        # Demonic layer toggle
        chk_demon = tk.Checkbutton(
            box, text="😈 Демонический дубль Аластора (питч -4 полутона, тремоло 5.5 Гц, хрипотца)",
            variable=self.demon_layer_var, bg="#181825", fg="#cba6f7", selectcolor="#11111b",
            activebackground="#181825", activeforeground="#cba6f7", font=("Segoe UI", 9, "bold")
        )
        chk_demon.pack(anchor="w", pady=(0, 6))

        # Vinyl toggle and intensity
        vinyl_row = tk.Frame(box, bg="#181825")
        vinyl_row.pack(fill=tk.X, pady=2)
        chk_vinyl = tk.Checkbutton(
            vinyl_row, text="Виниловый треск и шорох иглы", variable=self.vinyl_var,
            bg="#181825", fg="#cdd6f4", selectcolor="#11111b",
            activebackground="#181825", activeforeground="#cba6f7", font=("Segoe UI", 9)
        )
        chk_vinyl.pack(side=tk.LEFT)
        self.vinyl_val_lbl = tk.Label(vinyl_row, text=f"{self.vinyl_int_var.get():.1f}x", bg="#181825", fg="#cba6f7", font=("Segoe UI", 9, "bold"))
        self.vinyl_val_lbl.pack(side=tk.RIGHT)

        vinyl_slider = tk.Scale(
            box, from_=0.0, to=3.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.vinyl_int_var,
            bg="#181825", fg="#cdd6f4", troughcolor="#313244", highlightthickness=0, bd=0,
            showvalue=False, command=lambda v: self.vinyl_val_lbl.config(text=f"{float(v):.1f}x")
        )
        vinyl_slider.pack(fill=tk.X, pady=(0, 8))

        # Tube saturation / Drive
        drive_row = tk.Frame(box, bg="#181825")
        drive_row.pack(fill=tk.X, pady=2)
        tk.Label(drive_row, text="Ламповый перегруз (Drive dB):", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.drive_val_lbl = tk.Label(drive_row, text=f"{self.drive_var.get():.1f} dB", bg="#181825", fg="#cba6f7", font=("Segoe UI", 9, "bold"))
        self.drive_val_lbl.pack(side=tk.RIGHT)

        drive_slider = tk.Scale(
            box, from_=0.0, to=18.0, resolution=0.5, orient=tk.HORIZONTAL, variable=self.drive_var,
            bg="#181825", fg="#cdd6f4", troughcolor="#313244", highlightthickness=0, bd=0,
            showvalue=False, command=lambda v: self.drive_val_lbl.config(text=f"{float(v):.1f} dB")
        )
        drive_slider.pack(fill=tk.X, pady=(0, 8))

        # Cutoffs (Highpass / Lowpass)
        hp_row = tk.Frame(box, bg="#181825")
        hp_row.pack(fill=tk.X, pady=2)
        tk.Label(hp_row, text="Срез баса (Highpass):", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.hp_val_lbl = tk.Label(hp_row, text=f"{self.highpass_var.get()} Hz", bg="#181825", fg="#cba6f7", font=("Segoe UI", 9, "bold"))
        self.hp_val_lbl.pack(side=tk.RIGHT)

        hp_slider = tk.Scale(
            box, from_=50, to=800, orient=tk.HORIZONTAL, variable=self.highpass_var,
            bg="#181825", fg="#cdd6f4", troughcolor="#313244", highlightthickness=0, bd=0,
            showvalue=False, command=lambda v: self.hp_val_lbl.config(text=f"{int(v)} Hz")
        )
        hp_slider.pack(fill=tk.X, pady=(0, 6))

        lp_row = tk.Frame(box, bg="#181825")
        lp_row.pack(fill=tk.X, pady=2)
        tk.Label(lp_row, text="Срез высоких (Lowpass):", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.lp_val_lbl = tk.Label(lp_row, text=f"{self.lowpass_var.get()} Hz", bg="#181825", fg="#cba6f7", font=("Segoe UI", 9, "bold"))
        self.lp_val_lbl.pack(side=tk.RIGHT)

        lp_slider = tk.Scale(
            box, from_=1800, to=16000, orient=tk.HORIZONTAL, variable=self.lowpass_var,
            bg="#181825", fg="#cdd6f4", troughcolor="#313244", highlightthickness=0, bd=0,
            showvalue=False, command=lambda v: self.lp_val_lbl.config(text=f"{int(v)} Hz")
        )
        lp_slider.pack(fill=tk.X, pady=(0, 4))

    def _build_test_section(self, parent):
        box = tk.LabelFrame(
            parent, text=" 🧪 Тест голоса и фильтров в прямом эфире ",
            bg="#181825", fg="#89b4fa", font=("Segoe UI", 9, "bold"),
            padx=12, pady=10, bd=1, relief=tk.SOLID
        )
        box.pack(fill=tk.X, pady=(0, 10))

        self.test_text_entry = tk.Entry(
            box, bg="#11111b", fg="#cdd6f4", insertbackground="#cba6f7",
            font=("Segoe UI", 9), bd=0, highlightthickness=1, highlightcolor="#cba6f7", highlightbackground="#313244"
        )
        self.test_text_entry.insert(0, "Ха-ха! Шоу в эфире! Как звучит мой радио-голос, мой друг?")
        self.test_text_entry.pack(fill=tk.X, pady=(2, 8), ipady=4)

        btn_row = tk.Frame(box, bg="#181825")
        btn_row.pack(fill=tk.X)

        self.btn_test = tk.Button(
            btn_row, text="▶️ Прослушать тест", command=self._play_test,
            bg="#89b4fa", fg="#11111b", activebackground="#b4befe", font=("Segoe UI", 9, "bold"),
            bd=0, relief=tk.FLAT, padx=12, pady=4, cursor="hand2"
        )
        self.btn_test.pack(side=tk.LEFT)

        btn_stop = tk.Button(
            btn_row, text="⏹️ Стоп", command=self.tts.stop_speech,
            bg="#313244", fg="#f38ba8", activebackground="#45475a", font=("Segoe UI", 9),
            bd=0, relief=tk.FLAT, padx=10, pady=4, cursor="hand2"
        )
        btn_stop.pack(side=tk.LEFT, padx=8)

        self.status_lbl = tk.Label(
            btn_row, textvariable=self.status_var,
            bg="#181825", fg="#a6adc8", font=("Segoe UI", 9, "italic")
        )
        self.status_lbl.pack(side=tk.RIGHT)

    def _build_actions_bar(self):
        bar = tk.Frame(self.win, bg="#181825", padx=16, pady=10)
        bar.pack(side=tk.BOTTOM, fill=tk.X)

        btn_save = tk.Button(
            bar, text="💾 Сохранить и применить", command=self.save_and_apply,
            bg="#a6e3a1", fg="#11111b", activebackground="#94e2d5", font=("Segoe UI", 9, "bold"),
            bd=0, relief=tk.FLAT, padx=14, pady=5, cursor="hand2"
        )
        btn_save.pack(side=tk.LEFT)

        btn_reset = tk.Button(
            bar, text="🔄 Сброс в канон", command=self.reset_to_canon,
            bg="#313244", fg="#cdd6f4", activebackground="#45475a", font=("Segoe UI", 9),
            bd=0, relief=tk.FLAT, padx=10, pady=5, cursor="hand2"
        )
        btn_reset.pack(side=tk.LEFT, padx=8)

        btn_close = tk.Button(
            bar, text="Закрыть", command=self.win.destroy,
            bg="#313244", fg="#a6adc8", activebackground="#45475a", font=("Segoe UI", 9),
            bd=0, relief=tk.FLAT, padx=12, pady=5, cursor="hand2"
        )
        btn_close.pack(side=tk.RIGHT)

    def _on_voice_selected(self, event=None):
        selected_label = self.voice_combo.get()
        for code, label in VOICES_LIST:
            if label == selected_label:
                self.voice_var.set(code)
                break
        self.preset_var.set("Кастомный профиль")

    def _on_filter_selected(self, event=None):
        selected_label = self.filter_combo.get()
        for code, label in FILTERS_LIST:
            if label == selected_label:
                self.filter_var.set(code)
                # Apply filter profile defaults to sliders
                prof = DSP_PROFILES.get(code, {})
                if prof:
                    self.highpass_var.set(int(prof.get("highpass_hz", 350)))
                    self.hp_val_lbl.config(text=f"{int(prof.get('highpass_hz', 350))} Hz")
                    self.lowpass_var.set(int(prof.get("lowpass_hz", 3800)))
                    self.lp_val_lbl.config(text=f"{int(prof.get('lowpass_hz', 3800))} Hz")
                    self.drive_var.set(float(prof.get("drive_db", 6.0)))
                    self.drive_val_lbl.config(text=f"{float(prof.get('drive_db', 6.0)):.1f} dB")
                    self.vinyl_var.set(prof.get("add_vinyl", True))
                    self.vinyl_int_var.set(float(prof.get("vinyl_intensity", 1.0)))
                    self.vinyl_val_lbl.config(text=f"{float(prof.get('vinyl_intensity', 1.0)):.1f}x")
                    self.dsp_var.set(code != "clean")
                    self.demon_layer_var.set(prof.get("demon_layer", True))
                break
        self.preset_var.set("Кастомный профиль")

    def _on_preset_selected(self, event=None):
        title = self.preset_var.get()
        for key, p in VOICE_PRESETS.items():
            if p["title"] == title:
                # 1. Voice
                self.voice_var.set(p["voice"])
                for code, label in VOICES_LIST:
                    if code == p["voice"]:
                        self.voice_combo.set(label)
                        break

                # 2. Filter
                f_key = p.get("filter_profile", "canon_radio")
                self.filter_var.set(f_key)
                for code, label in FILTERS_LIST:
                    if code == f_key:
                        self.filter_combo.set(label)
                        break

                # 3. Rate & Pitch
                r_int = int(p["rate"].replace("%", "").replace("+", "") or 0)
                self.rate_var.set(r_int)
                self.rate_val_lbl.config(text=f"{r_int:+d}%")

                p_int = int(p["pitch"].replace("Hz", "").replace("+", "") or 0)
                self.pitch_var.set(p_int)
                self.pitch_val_lbl.config(text=f"{p_int:+d}Hz")

                # 4. Sliders
                self.dsp_var.set(p["dsp_enabled"])
                self.demon_layer_var.set(p.get("demon_layer", True))
                self.vinyl_var.set(p["add_vinyl"])
                self.vinyl_int_var.set(float(p["vinyl_intensity"]))
                self.vinyl_val_lbl.config(text=f"{p['vinyl_intensity']:.1f}x")


                self.highpass_var.set(int(p["highpass_hz"]))
                self.hp_val_lbl.config(text=f"{int(p['highpass_hz'])} Hz")

                self.lowpass_var.set(int(p["lowpass_hz"]))
                self.lp_val_lbl.config(text=f"{int(p['lowpass_hz'])} Hz")

                self.drive_var.set(float(p["drive_db"]))
                self.drive_val_lbl.config(text=f"{float(p['drive_db']):.1f} dB")
                break

    def _detect_active_preset(self):
        cur_v = self.voice_var.get()
        cur_f = self.filter_var.get()
        cur_r = f"{self.rate_var.get():+d}%"
        cur_p = f"{self.pitch_var.get():+d}Hz"
        cur_dsp = self.dsp_var.get()

        for key, p in VOICE_PRESETS.items():
            if (p["voice"] == cur_v and p.get("filter_profile") == cur_f and
                p["rate"] == cur_r and p["pitch"] == cur_p and p["dsp_enabled"] == cur_dsp):
                self.preset_var.set(p["title"])
                return
        self.preset_var.set("Кастомный профиль")

    def _gather_dict(self) -> dict:
        return {
            "voice": self.voice_var.get(),
            "filter_profile": self.filter_var.get(),
            "rate": f"{self.rate_var.get():+d}%",
            "pitch": f"{self.pitch_var.get():+d}Hz",
            "enabled": self.enabled_var.get(),
            "dsp_enabled": self.dsp_var.get(),
            "demon_layer": self.demon_layer_var.get(),
            "add_vinyl": self.vinyl_var.get(),
            "vinyl_intensity": round(self.vinyl_int_var.get(), 2),
            "highpass_hz": float(self.highpass_var.get()),
            "lowpass_hz": float(self.lowpass_var.get()),
            "drive_db": round(self.drive_var.get(), 1)
        }

    def _play_test(self):
        text = self.test_text_entry.get().strip()
        if not text:
            return

        settings = self._gather_dict()
        self.status_var.set("🎙️ Синтез речи...")
        self.btn_test.config(state=tk.DISABLED)

        def _done():
            self.win.after(100, lambda: [
                self.status_var.set("Готов к эфиру"),
                self.btn_test.config(state=tk.NORMAL)
            ])

        self.tts.test_sample(text, custom_settings=settings, on_finish=_done)

    def save_and_apply(self):
        settings = self._gather_dict()
        self.tts.apply_settings(settings, save=True)
        self.status_var.set("✓ Сохранено и активно!")
        log_info("Настройки голоса Аластора сохранены пользователем")
        self.win.after(2000, lambda: self.status_var.set("Готов к эфиру"))

    def reset_to_canon(self):
        self.preset_var.set(VOICE_PRESETS["alastor_canon"]["title"])
        self._on_preset_selected()
        self.save_and_apply()
