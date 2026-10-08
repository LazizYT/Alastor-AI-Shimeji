import os
import tkinter as tk
from tkinter import scrolledtext
from core.logger import get_recent_logs, clear_logs, get_log_filepath

class LogViewerWindow:
    def __init__(self, parent_root):
        self.parent = parent_root
        self.win = tk.Toplevel(self.parent)
        self.win.title("📜 Системный журнал (Логи) — Аластор")
        self.win.geometry("680x520")
        self.win.configure(bg="#11111b")
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.95)

        self.auto_refresh_var = tk.BooleanVar(value=True)
        self._last_log_count = 0
        self._after_id = None

        self._build_ui()
        self.refresh_logs()
        self._schedule_poll()

        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Header
        header = tk.Frame(self.win, bg="#181825", pady=8, padx=14)
        header.pack(fill=tk.X)

        title_lbl = tk.Label(
            header, text="📻 Журнал событий и радиоволн Аластора",
            font=("Segoe UI", 11, "bold"), fg="#cba6f7", bg="#181825"
        )
        title_lbl.pack(side=tk.LEFT)

        self.count_lbl = tk.Label(
            header, text="Записей: 0",
            font=("Segoe UI", 9), fg="#a6adc8", bg="#181825"
        )
        self.count_lbl.pack(side=tk.RIGHT)

        # Main Log Area
        self.text_area = scrolledtext.ScrolledText(
            self.win, wrap=tk.WORD, state=tk.DISABLED,
            bg="#181825", fg="#cdd6f4", font=("Consolas", 10),
            bd=0, padx=12, pady=10, highlightthickness=0
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # Color Tags
        self.text_area.tag_configure("TIME", foreground="#6c7086")
        self.text_area.tag_configure("INFO", foreground="#89b4fa")
        self.text_area.tag_configure("VOICE", foreground="#a6e3a1", font=("Consolas", 10, "bold"))
        self.text_area.tag_configure("AI", foreground="#cba6f7", font=("Consolas", 10, "bold"))
        self.text_area.tag_configure("WARN", foreground="#f9e2af")
        self.text_area.tag_configure("ERROR", foreground="#f38ba8", font=("Consolas", 10, "bold"))
        self.text_area.tag_configure("MSG", foreground="#cdd6f4")

        # Bottom Bar
        bar = tk.Frame(self.win, bg="#11111b", padx=10, pady=8)
        bar.pack(fill=tk.X)

        chk = tk.Checkbutton(
            bar, text="Автообновление (2с)", variable=self.auto_refresh_var,
            bg="#11111b", fg="#cdd6f4", selectcolor="#181825",
            activebackground="#11111b", activeforeground="#cba6f7",
            font=("Segoe UI", 9)
        )
        chk.pack(side=tk.LEFT)

        btn_open = tk.Button(
            bar, text="📂 Открыть файл логов", command=self.open_log_file,
            bg="#313244", fg="#cdd6f4", activebackground="#45475a",
            bd=0, relief=tk.FLAT, padx=10, pady=3, font=("Segoe UI", 9), cursor="hand2"
        )
        btn_open.pack(side=tk.RIGHT, padx=(6, 0))

        btn_clear = tk.Button(
            bar, text="🧹 Очистить", command=self.clear_all,
            bg="#313244", fg="#f38ba8", activebackground="#45475a",
            bd=0, relief=tk.FLAT, padx=10, pady=3, font=("Segoe UI", 9), cursor="hand2"
        )
        btn_clear.pack(side=tk.RIGHT, padx=(6, 0))

        btn_ref = tk.Button(
            bar, text="🔄 Обновить", command=self.refresh_logs,
            bg="#45475a", fg="#cdd6f4", activebackground="#585b70",
            bd=0, relief=tk.FLAT, padx=12, pady=3, font=("Segoe UI", 9, "bold"), cursor="hand2"
        )
        btn_ref.pack(side=tk.RIGHT)

    def refresh_logs(self):
        logs = get_recent_logs()
        self._last_log_count = len(logs)
        self.count_lbl.config(text=f"Записей: {self._last_log_count}")

        self.text_area.configure(state=tk.NORMAL)
        self.text_area.delete("1.0", tk.END)

        for entry in logs:
            t = entry["time"]
            lvl = entry["level"]
            msg = entry["message"]

            self.text_area.insert(tk.END, f"[{t}] ", "TIME")
            self.text_area.insert(tk.END, f"[{lvl:5}] ", lvl if lvl in ("INFO", "VOICE", "AI", "WARN", "ERROR") else "INFO")
            self.text_area.insert(tk.END, f"{msg}\n", "MSG")

        self.text_area.configure(state=tk.DISABLED)
        self.text_area.see(tk.END)

    def _schedule_poll(self):
        if self.auto_refresh_var.get():
            logs = get_recent_logs()
            if len(logs) != self._last_log_count:
                self.refresh_logs()
        self._after_id = self.win.after(2000, self._schedule_poll)

    def open_log_file(self):
        fp = get_log_filepath()
        if os.path.exists(fp):
            try:
                os.startfile(fp)
            except Exception:
                pass

    def clear_all(self):
        clear_logs()
        self.refresh_logs()

    def _on_close(self):
        if self._after_id:
            try:
                self.win.after_cancel(self._after_id)
            except Exception:
                pass
        self.win.destroy()
