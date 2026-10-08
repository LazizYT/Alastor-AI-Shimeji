import os
import re
import threading
from core.logger import log_info, log_warn, log_error

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False


class MediaDownloader:
    """
    Downloads audio or video tracks from YouTube, TikTok, VK, etc. via yt-dlp.
    Saves media directly to the user's Downloads/Alastor_Media folder.
    """

    def __init__(self):
        self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Alastor_Media")
        os.makedirs(self.download_dir, exist_ok=True)
        self.is_downloading = False

    @staticmethod
    def extract_url(text: str) -> str | None:
        """Extracts the first HTTP/HTTPS URL from a string."""
        if not text:
            return None
        match = re.search(r'https?://[^\s<>"]+', text)
        if match:
            return match.group(0).rstrip(".,;!?:)'\"")
        return None

    def start_download(self, url: str, audio_only: bool = True, on_complete=None) -> tuple[bool, str]:
        """
        Starts downloading the media in a non-blocking background thread.
        Returns immediate status: (started: bool, message: str)
        """
        if not YT_DLP_AVAILABLE:
            return False, "Библиотека yt-dlp не установлена! 📦"

        clean_url = self.extract_url(url)
        if not clean_url:
            return False, "В тексте или буфере обмена нет действующей ссылки для скачивания! 🔗"

        if self.is_downloading:
            return False, "Предыдущая загрузка ещё идёт! Дай мне секунду завершить передачу... ⏳"

        self.is_downloading = True

        def _worker():
            try:
                log_info(f"Начало загрузки медиа: {clean_url} (audio_only={audio_only})")
                out_tmpl = os.path.join(self.download_dir, "%(title).80s.%(ext)s")

                ydl_opts = {
                    "outtmpl": out_tmpl,
                    "quiet": True,
                    "no_warnings": True,
                    "nocheckcertificate": True,
                    "ignoreerrors": False
                }

                if audio_only:
                    ydl_opts.update({
                        "format": "bestaudio/best",
                        "postprocessors": [{
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192"
                        }]
                    })
                else:
                    ydl_opts.update({
                        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                    })

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(clean_url, download=True)
                    title = info.get("title", "Медиафайл")

                log_info(f"Загрузка успешно завершена: «{title}»")
                msg = f"Ха-ха! Запись «{title[:40]}» успешно перехвачена и сохранена в папку Alastor_Media! 🎶📻"
                if on_complete:
                    on_complete(True, msg, self.download_dir)
            except Exception as e:
                log_error(f"Ошибка загрузки медиа: {e}")
                err_msg = f"Помехи в эфире! Не удалось загрузить: {str(e)[:50]}... 📻"
                if on_complete:
                    on_complete(False, err_msg, self.download_dir)
            finally:
                self.is_downloading = False

        threading.Thread(target=_worker, daemon=True).start()
        media_type = "аудио (MP3)" if audio_only else "видео (MP4)"
        return True, f"Запускаю перехват радиоволн! Скачиваю {media_type}... 📥✨"
