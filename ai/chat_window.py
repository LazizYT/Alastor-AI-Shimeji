import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
from core.config import REQUESTS_AVAILABLE
from core.logger import log_ai, log_error, log_info
from ai.alastor_brain import ALASTOR_SYSTEM_PROMPT
from ai.gemini_client import query_gemini, verify_gemini_connection
from ai.vision_engine import VisionEngine

class ChatWindow:
    def __init__(self, parent_root, api_key_var, shimeji_ref):
        self.parent      = parent_root
        self.api_key_var = api_key_var
        self.shimeji     = shimeji_ref
        self.history     = []
        self.mode_var    = tk.StringVar(value="api" if api_key_var.get() else "local")
        self.local_pipe  = None
        self.vision_engine = getattr(shimeji_ref, "vision_engine", None) or VisionEngine()
        
        # Provider vars
        self.openrouter_key_var = tk.StringVar(value=self.vision_engine.config.get("openrouter_api_key", ""))
        self.opencode_key_var   = tk.StringVar(value=self.vision_engine.config.get("opencode_api_key", ""))
        self.opencode_url_var   = tk.StringVar(value=self.vision_engine.config.get("opencode_base_url", "https://api.opencode.ai/v1"))
        self.ollama_url_var     = tk.StringVar(value=self.vision_engine.config.get("ollama_url", "http://localhost:11434"))
        self.show_settings      = tk.BooleanVar(value=False)

        self._build_window()

    def _build_window(self):
        self.win = tk.Toplevel(self.parent)
        self.win.title("🎙️ Радио-чат с Аластором")
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.92)
        self.win.configure(bg="#11111b")
        self.win.geometry("490x650")
        self.win.minsize(440, 500)

        # Header
        header = tk.Frame(self.win, bg="#181825", pady=8, padx=12)
        header.pack(fill=tk.X)
        tk.Label(header, text="✨ Радио-демон Аластор ✨", font=("Segoe UI", 12, "bold"), fg="#cba6f7", bg="#181825").pack(side=tk.LEFT)
        
        self.settings_toggle_btn = tk.Button(
            header, text="⚙️ Провайдеры / API", command=self._toggle_settings_panel,
            bg="#313244", fg="#cdd6f4", font=("Segoe UI", 8),
            activebackground="#45475a", bd=0, relief=tk.FLAT, padx=8, pady=2, cursor="hand2"
        )
        self.settings_toggle_btn.pack(side=tk.RIGHT)

        # Mode Selection Bar
        mode_frame = tk.Frame(self.win, bg="#11111b", pady=4, padx=12)
        mode_frame.pack(fill=tk.X)
        
        rb_api = tk.Radiobutton(
            mode_frame, text="API (Gemini + Multi-Vision Fallback)", variable=self.mode_var, value="api",
            bg="#11111b", fg="#cdd6f4", selectcolor="#181825", activebackground="#11111b",
            activeforeground="#cba6f7", font=("Segoe UI", 9), command=self._toggle_mode
        )
        rb_api.pack(side=tk.LEFT, padx=(0, 10))

        rb_local = tk.Radiobutton(
            mode_frame, text="Локальная (SmolLM2)", variable=self.mode_var, value="local",
            bg="#11111b", fg="#cdd6f4", selectcolor="#181825", activebackground="#11111b",
            activeforeground="#cba6f7", font=("Segoe UI", 9), command=self._toggle_mode
        )
        rb_local.pack(side=tk.LEFT)

        # Expandable Provider Settings Panel
        self.settings_frame = tk.Frame(self.win, bg="#181825", padx=12, pady=8, highlightbackground="#313244", highlightthickness=1)
        
        # Row 1: Gemini Key
        r1 = tk.Frame(self.settings_frame, bg="#181825")
        r1.pack(fill=tk.X, pady=2)
        tk.Label(r1, text="🔑 Gemini Key:", bg="#181825", fg="#a6adc8", font=("Segoe UI", 8, "bold"), width=15, anchor="w").pack(side=tk.LEFT)
        self.api_entry = tk.Entry(r1, textvariable=self.api_key_var, show="*", bg="#313244", fg="#cdd6f4", insertbackground="white", font=("Segoe UI", 8), bd=0)
        self.api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Row 2: OpenRouter Key
        r2 = tk.Frame(self.settings_frame, bg="#181825")
        r2.pack(fill=tk.X, pady=2)
        tk.Label(r2, text="🌐 OpenRouter Key:", bg="#181825", fg="#a6adc8", font=("Segoe UI", 8, "bold"), width=15, anchor="w").pack(side=tk.LEFT)
        self.or_entry = tk.Entry(r2, textvariable=self.openrouter_key_var, show="*", bg="#313244", fg="#cdd6f4", insertbackground="white", font=("Segoe UI", 8), bd=0)
        self.or_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Row 3: OpenCode Key / URL
        r3 = tk.Frame(self.settings_frame, bg="#181825")
        r3.pack(fill=tk.X, pady=2)
        tk.Label(r3, text="💻 OpenCode Key:", bg="#181825", fg="#a6adc8", font=("Segoe UI", 8, "bold"), width=15, anchor="w").pack(side=tk.LEFT)
        self.oc_entry = tk.Entry(r3, textvariable=self.opencode_key_var, show="*", bg="#313244", fg="#cdd6f4", insertbackground="white", font=("Segoe UI", 8), bd=0)
        self.oc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Row 4: Ollama Local URL
        r4 = tk.Frame(self.settings_frame, bg="#181825")
        r4.pack(fill=tk.X, pady=2)
        tk.Label(r4, text="🦙 Ollama URL:", bg="#181825", fg="#a6adc8", font=("Segoe UI", 8, "bold"), width=15, anchor="w").pack(side=tk.LEFT)
        self.ol_entry = tk.Entry(r4, textvariable=self.ollama_url_var, bg="#313244", fg="#cdd6f4", insertbackground="white", font=("Segoe UI", 8), bd=0)
        self.ol_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Save and Verify buttons
        btn_box = tk.Frame(self.settings_frame, bg="#181825", pady=4)
        btn_box.pack(fill=tk.X)
        save_btn = tk.Button(
            btn_box, text="💾 Сохранить ключи", command=self._save_keys,
            bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 8, "bold"), bd=0, relief=tk.FLAT, padx=8, pady=2, cursor="hand2"
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.verify_btn = tk.Button(
            btn_box, text="🔍 Тест подключения ИИ", command=self.verify_connection,
            bg="#313244", fg="#cdd6f4", font=("Segoe UI", 8, "bold"),
            activebackground="#45475a", bd=0, relief=tk.FLAT, padx=8, pady=2, cursor="hand2"
        )
        self.verify_btn.pack(side=tk.LEFT)

        # Chat display area
        self.chat_area = scrolledtext.ScrolledText(
            self.win, wrap=tk.WORD, state=tk.DISABLED,
            bg="#181825", fg="#cdd6f4", font=("Segoe UI", 10),
            bd=0, padx=12, pady=12, highlightthickness=0
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
        self.chat_area.tag_configure("user", foreground="#89b4fa", font=("Segoe UI", 10, "bold"))
        self.chat_area.tag_configure("bot", foreground="#f38ba8", font=("Segoe UI", 10))
        self.chat_area.tag_configure("system", foreground="#a6adc8", font=("Segoe UI", 9, "italic"))
        self.chat_area.tag_configure("vision", foreground="#cba6f7", font=("Segoe UI", 9, "bold"))

        # Input Frame
        inp = tk.Frame(self.win, bg="#11111b", padx=12, pady=8)
        inp.pack(fill=tk.X)
        
        self.entry = tk.Entry(
            inp, bg="#313244", fg="#cdd6f4",
            insertbackground="white",
            font=("Segoe UI", 10), bd=0, relief=tk.FLAT
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 6))
        self.entry.bind("<Return>", lambda e: self.send_message())
        self.entry.focus()
        
        # Mute toggle button
        is_muted = getattr(self.shimeji, "is_muted", False)
        mute_icon = "🔇" if is_muted else "🔊"
        self.mute_btn = tk.Button(
            inp, text=mute_icon, command=self._toggle_mute,
            bg="#313244", fg="#cdd6f4",
            font=("Segoe UI", 10, "bold"),
            activebackground="#45475a",
            bd=0, relief=tk.FLAT, padx=8, cursor="hand2"
        )
        self.mute_btn.pack(side=tk.RIGHT)

        # Send button
        self.send_btn = tk.Button(
            inp, text="Отправить 🚀", command=self.send_message,
            bg="#cba6f7", fg="#11111b",
            font=("Segoe UI", 9, "bold"),
            activebackground="#b4befe",
            bd=0, relief=tk.FLAT, padx=10, cursor="hand2"
        )
        self.send_btn.pack(side=tk.RIGHT, padx=(0, 4))
        
        # Vision button
        self.vision_btn = tk.Button(
            inp, text="👀 Экран", command=self._trigger_vision,
            bg="#45475a", fg="#cba6f7",
            font=("Segoe UI", 9, "bold"),
            activebackground="#585b70",
            bd=0, relief=tk.FLAT, padx=8, cursor="hand2"
        )
        self.vision_btn.pack(side=tk.RIGHT, padx=(0, 4))

        # Clipboard explain button
        self.clip_btn = tk.Button(
            inp, text="📋", command=self._trigger_clipboard,
            bg="#45475a", fg="#cdd6f4",
            font=("Segoe UI", 9, "bold"),
            activebackground="#585b70",
            bd=0, relief=tk.FLAT, padx=6, cursor="hand2"
        )
        self.clip_btn.pack(side=tk.RIGHT, padx=(0, 4))

        # Media download button
        self.dl_btn = tk.Button(
            inp, text="📥", command=self._trigger_download,
            bg="#45475a", fg="#cdd6f4",
            font=("Segoe UI", 9, "bold"),
            activebackground="#585b70",
            bd=0, relief=tk.FLAT, padx=6, cursor="hand2"
        )
        self.dl_btn.pack(side=tk.RIGHT, padx=(0, 4))

        # Voice record button
        self.voice_btn = tk.Button(
            inp, text="🎤", command=self.shimeji.start_voice_capture,
            bg="#45475a", fg="#cdd6f4",
            font=("Segoe UI", 9, "bold"),
            activebackground="#585b70",
            bd=0, relief=tk.FLAT, padx=8, cursor="hand2"
        )
        self.voice_btn.pack(side=tk.RIGHT, padx=(0, 4))
        
        self.append_message("system", "🎙️ В эфире Радио-демон! Задавай свои вопросы, либо нажми [👀 Экран], чтобы я взглянул на происходящее...\n")

    def _toggle_settings_panel(self):
        cur = self.show_settings.get()
        if cur:
            self.settings_frame.pack_forget()
            self.show_settings.set(False)
        else:
            self.settings_frame.pack(fill=tk.X, padx=12, pady=(0, 6), before=self.chat_area)
            self.show_settings.set(True)

    def _toggle_mode(self):
        pass

    def _save_keys(self):
        g_key = self.api_key_var.get().strip()
        or_key = self.openrouter_key_var.get().strip()
        oc_key = self.opencode_key_var.get().strip()
        oc_url = self.opencode_url_var.get().strip()
        ol_url = self.ollama_url_var.get().strip()

        cfg = {
            "gemini_api_key": g_key,
            "openrouter_api_key": or_key,
            "opencode_api_key": oc_key,
            "opencode_base_url": oc_url,
            "ollama_url": ol_url
        }
        self.vision_engine.save_config(cfg)
        self.append_message("system", "💾 Настройки провайдеров (Gemini, OpenRouter, OpenCode, Ollama) сохранены!\n")

    def _toggle_mute(self):
        if hasattr(self.shimeji, "toggle_mute"):
            self.shimeji.toggle_mute()
            is_muted = getattr(self.shimeji, "is_muted", False)
            self.mute_btn.configure(text="🔇" if is_muted else "🔊")
            st = "заглушён 🔇" if is_muted else "включён 🔊"
            self.append_message("system", f"Статус звука: {st}\n")

    def append_message(self, tag, text):
        self.chat_area.configure(state=tk.NORMAL)
        self.chat_area.insert(tk.END, text, tag)
        self.chat_area.configure(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    def verify_connection(self):
        self.verify_btn.configure(state=tk.DISABLED, text="Проверка...")
        threading.Thread(target=self._run_verification, daemon=True).start()

    def _run_verification(self):
        api_key = self.api_key_var.get().strip()
        ok, msg = verify_gemini_connection(api_key)
        if ok:
            self.parent.after(0, lambda: self.append_message("system", f"✅ {msg}\n"))
        else:
            self.parent.after(0, lambda: self.append_message("system", f"ℹ️ Gemini: {msg}. Проверяю цепочку fallback...\n"))

        # Check Ollama status
        try:
            import requests
            ol_url = self.ollama_url_var.get().strip() or "http://localhost:11434"
            r = requests.get(f"{ol_url}/api/tags", timeout=2)
            if r.status_code == 200:
                self.parent.after(0, lambda: self.append_message("system", f"✅ Ollama онлайн ({ol_url})\n"))
            else:
                self.parent.after(0, lambda: self.append_message("system", "ℹ️ Ollama не отвечает\n"))
        except Exception:
            self.parent.after(0, lambda: self.append_message("system", "ℹ️ Ollama не запущена (локальный порт 11434 закрыт)\n"))

        self.parent.after(0, lambda: self.verify_btn.configure(state=tk.NORMAL, text="🔍 Тест подключения ИИ"))

    def _trigger_vision(self, custom_prompt: str = None):
        user_p = custom_prompt or self.entry.get().strip()
        if not custom_prompt:
            self.entry.delete(0, tk.END)

        if user_p:
            self.append_message("user", f"Вы (запрос к экрану): {user_p}\n")
        else:
            self.append_message("user", "Вы: 👀 Что происходит на моём экране?\n")

        self.append_message("vision", "👁️ Аластор всматривается в происходящее на экране (Fallback: Gemini → OpenRouter → OpenCode → Ollama)...\n")
        self.vision_btn.configure(state=tk.DISABLED, text="👀 Анализ...")

        def _worker():
            ok, reply, prov = self.vision_engine.analyze_screen(user_p)
            self.parent.after(0, lambda: self._show_vision_reply(reply, prov))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_vision_reply(self, reply: str, prov: str):
        self.append_message("vision", f"[{prov}]\n")
        self.append_message("bot", f"Аластор: {reply}\n\n")
        self.vision_btn.configure(state=tk.NORMAL, text="👀 Экран")
        log_ai(f"Ответ зрения Аластора [{prov}]: {reply[:60]}")
        self.shimeji.show_speech(reply[:70] + "...", play_audio=True)

    def _trigger_clipboard(self):
        if hasattr(self.shimeji, "action_explain_clipboard"):
            self.append_message("system", "📋 Запрос к буферу обмена...\n")
            self.shimeji.action_explain_clipboard()

    def _trigger_download(self):
        if hasattr(self.shimeji, "action_download_media"):
            text = self.entry.get().strip()
            self.entry.delete(0, tk.END)
            self.append_message("system", "📥 Запрос на скачивание медиа...\n")
            self.shimeji.action_download_media(audio_only=True, url=text or None)

    def send_message(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self.append_message("user", f"Вы: {text}\n")
        
        low = text.lower()

        # Check Vision query
        if any(w in low for w in ["что ты видишь", "посмотри на экран", "что на экране", "опиши экран", "взгляни на экран", "посмотри вокруг", "что видишь"]):
            self._trigger_vision(custom_prompt=text)
            return

        # Check Mute query
        if any(w in low for w in ["замолчи", "тихо", "без звука", "выключи звук", "заглуши", "мут", "mute"]):
            self.shimeji.set_mute(True)
            self.mute_btn.configure(text="🔇")
            self.append_message("system", "🔇 Трансляция заглушена (Mute активирован).\n\n")
            return

        if any(w in low for w in ["включи звук", "звук включи", "говори", "размут", "размуть", "unmute"]):
            self.shimeji.set_mute(False)
            self.mute_btn.configure(text="🔊")
            self.append_message("system", "🔊 Звук включён! Радио-эфир снова на связи.\n\n")
            return

        # Check Memory query
        if hasattr(self.shimeji, 'memory'):
            self.shimeji.memory.extract_facts(text)
            self.shimeji.memory.record_interaction()

        if hasattr(self.shimeji, 'command_router'):
            handled, reply = self.shimeji.command_router.route_command(text)
            if handled and reply:
                self._show_reply(reply)
                return

        self.send_btn.configure(state=tk.DISABLED, text="…")
        
        if self.mode_var.get() == "api":
            self.history.append({"role": "user", "parts": [{"text": text}]})
            threading.Thread(target=self._call_api, daemon=True).start()
        else:
            threading.Thread(target=self._call_local, args=(text,), daemon=True).start()

    def _call_local(self, text):
        try:
            from transformers import pipeline
            if not self.local_pipe:
                self.parent.after(0, lambda: self.append_message("system", "⏳ Загрузка SmolLM2 в память...\n"))
                self.local_pipe = pipeline("text-generation", model="HuggingFaceTB/SmolLM2-135M-Instruct")
            
            mem_ctx = self.shimeji.memory.get_prompt_context() if hasattr(self.shimeji, 'memory') else ""
            sys_prompt = f"{ALASTOR_SYSTEM_PROMPT}\n\n{mem_ctx}" if mem_ctx else ALASTOR_SYSTEM_PROMPT
            msgs = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": text}
            ]
            out = self.local_pipe(msgs, max_new_tokens=60)
            reply = out[0]['generated_text'][-1]['content']
            self.parent.after(0, self._show_reply, reply)
        except Exception:
            from ai.alastor_brain import generate_alastor_reply
            reply = generate_alastor_reply(text)
            self.parent.after(0, self._show_reply, reply)

    def _call_api(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            self._show_error("Укажите ваш API-ключ Gemini или настройте OpenRouter в панели настроек!")
            return
        if not REQUESTS_AVAILABLE:
            self._show_error("Отсутствует библиотека requests")
            return
            
        try:
            mem_ctx = self.shimeji.memory.get_prompt_context() if hasattr(self.shimeji, 'memory') else ""
            sys_prompt = f"{ALASTOR_SYSTEM_PROMPT}\n\n{mem_ctx}" if mem_ctx else ALASTOR_SYSTEM_PROMPT
            reply = query_gemini(api_key, self.history, sys_prompt, max_tokens=1024)
            self.history.append({"role": "model", "parts": [{"text": reply}]})
            self.parent.after(0, self._show_reply, reply)
        except Exception as e:
            self._show_error(f"Ошибка вызова API Gemini (проверьте ключ): {e}")

    def _show_reply(self, reply):
        self.append_message("bot", f"Аластор: {reply}\n\n")
        self.send_btn.configure(state=tk.NORMAL, text="Отправить 🚀")
        log_ai(f"Ответ Аластора в чате: {reply[:60]}")
        self.shimeji.show_speech(reply[:70] + "...", play_audio=True)

    def _show_error(self, msg):
        log_error(f"Ошибка чата: {msg}")
        self.parent.after(0, lambda: (
            self.append_message("system", f"⚠ {msg}\n"),
            self.send_btn.configure(state=tk.NORMAL, text="Отправить 🚀")
        ))
