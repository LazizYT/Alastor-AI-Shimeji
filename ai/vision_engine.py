import os
import io
import json
import base64
import time
import requests
from PIL import Image
from core.config import AI_CONFIG_FILE, BASE_DIR
from core.logger import log_info, log_warn, log_error, log_ai

# -------------------------------------------------------------------------
# Verified Vision Models Config
# -------------------------------------------------------------------------
GEMINI_VISION_MODELS = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-2.5-pro"
]

OPENROUTER_FREE_VISION_MODELS = [
    "qwen/qwen3.8-27b:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "dots-studio/dots-3-note-preview:free",
    "openrouter/free"
]

OPENCODE_VISION_MODELS = [
    "opencode/zen-vision",
    "opencode/free",
    "google/gemini-2.0-flash",
    "meta-llama/llama-3.2-11b-vision"
]

OLLAMA_VISION_MODELS = [
    "llama3.2-vision",
    "llava",
    "qwen2.5-vl",
    "minicpm-v",
    "bakllava"
]

DEFAULT_VISION_PROMPT = (
    "Ты — Аластор, легендарный Радио-демон из Hazbin Hotel. "
    "Перед тобой снимок экрана пользователя. "
    "Опиши кратко (2-4 предложения), что ты видишь на экране: какие окна открыты, чем занят пользователь, "
    "и добавь свой фирменный радио-комментарий — остроумный, слегка насмешливый, артистичный и непременно с улыбкой! "
    "Используй радио-метафоры и винтажный стиль 1920-х годов. Отвечай только на русском языке."
)

DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "openrouter_api_key": "",
    "opencode_api_key": "",
    "opencode_base_url": "https://api.opencode.ai/v1",
    "ollama_url": "http://localhost:11434",
    "preferred_provider": "fallback"
}


class VisionEngine:
    """
    Handles screenshot capture and multimodal vision analysis across
    Gemini, OpenRouter, OpenCode, and local Ollama with a fault-tolerant fallback chain.
    """

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> dict:
        cfg = dict(DEFAULT_CONFIG)
        if os.path.exists(AI_CONFIG_FILE):
            try:
                with open(AI_CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    cfg.update(saved)
            except Exception as e:
                log_error(f"Не удалось загрузить {AI_CONFIG_FILE}: {e}")

        # Check environment variables fallback
        if not cfg.get("gemini_api_key"):
            cfg["gemini_api_key"] = os.environ.get("GOOGLE_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
        if not cfg.get("openrouter_api_key"):
            cfg["openrouter_api_key"] = os.environ.get("OPENROUTER_API_KEY", "")
        if not cfg.get("opencode_api_key"):
            cfg["opencode_api_key"] = os.environ.get("OPENCODE_API_KEY", "")

        return cfg

    def save_config(self, new_cfg: dict):
        self.config.update(new_cfg)
        try:
            with open(AI_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            log_info("Конфигурация ИИ и зрения сохранена")
        except Exception as e:
            log_error(f"Ошибка сохранения {AI_CONFIG_FILE}: {e}")

    def verify_connection(self) -> dict:
        """Verifies configured keys and endpoints for Gemini, OpenRouter, OpenCode, and Ollama."""
        results = {}
        g_key = self.config.get("gemini_api_key", "").strip()
        results["Gemini"] = "Ключ сконфигурирован" if g_key else "Ключ не задан (пропуск в fallback)"

        or_key = self.config.get("openrouter_api_key", "").strip()
        results["OpenRouter"] = "Ключ задан" if or_key else "Free-tier fallback"

        oc_key = self.config.get("opencode_api_key", "").strip()
        oc_url = self.config.get("opencode_base_url", "https://api.opencode.ai/v1")
        results["OpenCode"] = f"Endpoint: {oc_url} ({'ключ задан' if oc_key else 'без ключа'})"

        ol_url = self.config.get("ollama_url", "http://localhost:11434").strip()
        try:
            r = requests.get(f"{ol_url}/api/tags", timeout=1.5)
            if r.status_code == 200:
                results["Ollama"] = f"Онлайн ({ol_url})"
            else:
                results["Ollama"] = f"Код {r.status_code}"
        except Exception:
            results["Ollama"] = f"Не запущена ({ol_url})"

        return results

    # -------------------------------------------------------------------------
    # Screenshot Capture
    # -------------------------------------------------------------------------
    def take_screenshot(self, max_dim: int = 1024, quality: int = 80) -> tuple[Image.Image, str, bytes]:
        """
        Captures the screen using multi-tier fallback (mss -> ImageGrab -> pyautogui -> Win32 GDI).
        Resizes to max_dim and encodes to JPEG bytes and base64 string.
        """
        img = None

        # 1. Try mss (fastest and handles multi-monitor)
        try:
            import mss
            with mss.mss() as sct:
                monitor = sct.monitors[0]  # Full virtual screen
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        except Exception:
            pass

        # 2. Try PIL.ImageGrab
        if img is None:
            try:
                from PIL import ImageGrab
                img = ImageGrab.grab(all_screens=True)
            except Exception:
                pass

        # 3. Try PyAutoGUI
        if img is None:
            try:
                import pyautogui
                img = pyautogui.screenshot()
            except Exception:
                pass

        # 4. Fallback canvas if non-interactive environment
        if img is None:
            log_warn("Не удалось получить аппаратный снимок экрана. Создаю тестовый кадр.")
            img = Image.new("RGB", (800, 600), color=(24, 24, 37))
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.rectangle([50, 50, 750, 550], fill=(49, 50, 68), outline=(203, 166, 247), width=3)
            draw.text((80, 80), "Alastor Radio Station - Screen Capture Stream", fill=(205, 214, 244))

        # Convert to RGB
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Resize preserving aspect ratio so largest dimension <= max_dim
        w, h = img.size
        if max(w, h) > max_dim:
            scale = max_dim / float(max(w, h))
            nw = int(w * scale)
            nh = int(h * scale)
            img = img.resize((nw, nh), Image.Resampling.LANCZOS)

        # Compress to JPEG
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        raw_bytes = buf.getvalue()
        b64_str = base64.b64encode(raw_bytes).decode("ascii")

        return img, b64_str, raw_bytes

    def capture_screen(self, max_dim: int = 1024, quality: int = 80) -> bytes:
        """Helper returning raw JPEG bytes of screen capture."""
        _, _, raw_bytes = self.take_screenshot(max_dim=max_dim, quality=quality)
        return raw_bytes

    # -------------------------------------------------------------------------
    # Provider 1: Gemini Vision
    # -------------------------------------------------------------------------
    def _call_gemini(self, b64_img: str, prompt: str, key: str) -> tuple[bool, str, str]:
        if not key:
            return False, "", "Gemini: API-ключ не указан"

        for model in GEMINI_VISION_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": b64_img
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.85,
                    "maxOutputTokens": 2048,
                    "thinkingConfig": {
                        "thinkingBudget": 256
                    }
                }
            }
            try:
                resp = requests.post(url, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            text = parts[0].get("text", "").strip()
                            if text:
                                return True, text, f"Gemini ({model})"
                elif resp.status_code in (429, 503):
                    log_warn(f"Gemini {model} вернул статус {resp.status_code} (лимит/нагрузка), короткая пауза...")
                    time.sleep(1.5)
                else:
                    log_warn(f"Gemini {model} вернул статус {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                log_warn(f"Ошибка вызова Gemini {model}: {e}")

        return False, "", "Gemini: Все модели вернули ошибку или недоступны"

    # -------------------------------------------------------------------------
    # Provider 2: OpenRouter Free Vision
    # -------------------------------------------------------------------------
    def _call_openrouter(self, b64_img: str, prompt: str, key: str) -> tuple[bool, str, str]:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/shimeji-alastor",
            "X-Title": "Alastor Shimeji Radio Demon"
        }
        if key:
            headers["Authorization"] = f"Bearer {key}"

        for model in OPENROUTER_FREE_VISION_MODELS:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64_img}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 600,
                "temperature": 0.85
            }
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        msg = choices[0].get("message", {}).get("content", "").strip()
                        if msg:
                            return True, msg, f"OpenRouter ({model})"
                elif resp.status_code == 401 and not key:
                    log_warn("OpenRouter требует бесплатный API-ключ (создаётся на openrouter.ai)")
                    break
                else:
                    log_warn(f"OpenRouter {model} ошибка {resp.status_code}: {resp.text[:100]}")
            except Exception as e:
                log_warn(f"Ошибка вызова OpenRouter {model}: {e}")

        return False, "", "OpenRouter: Модели недоступны или исчерпан лимит"

    # -------------------------------------------------------------------------
    # Provider 3: OpenCode Vision
    # -------------------------------------------------------------------------
    def _call_opencode(self, b64_img: str, prompt: str, key: str, base_url: str) -> tuple[bool, str, str]:
        endpoint = base_url.rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"

        for model in OPENCODE_VISION_MODELS:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64_img}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 600
            }
            try:
                resp = requests.post(endpoint, headers=headers, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        msg = choices[0].get("message", {}).get("content", "").strip()
                        if msg:
                            return True, msg, f"OpenCode ({model})"
            except Exception as e:
                log_warn(f"Ошибка вызова OpenCode {model}: {e}")

        return False, "", "OpenCode: Сервис недоступен"

    # -------------------------------------------------------------------------
    # Provider 4: Ollama Local Vision
    # -------------------------------------------------------------------------
    def _call_ollama(self, b64_img: str, prompt: str, base_url: str) -> tuple[bool, str, str]:
        tags_url = base_url.rstrip("/") + "/api/tags"
        try:
            chk = requests.get(tags_url, timeout=3)
            if chk.status_code != 200:
                return False, "", "Ollama: Сервер не отвечает"
            
            models_info = chk.json().get("models", [])
            installed_names = [m.get("name", "") for m in models_info]
        except Exception:
            return False, "", "Ollama: Локальный сервер не запущен"

        # Select matching vision model
        chosen_model = None
        for cand in OLLAMA_VISION_MODELS:
            for inst in installed_names:
                if cand in inst:
                    chosen_model = inst
                    break
            if chosen_model:
                break

        if not chosen_model:
            chosen_model = "llama3.2-vision"

        gen_url = base_url.rstrip("/") + "/api/generate"
        payload = {
            "model": chosen_model,
            "prompt": prompt,
            "images": [b64_img],
            "stream": False
        }
        try:
            resp = requests.post(gen_url, json=payload, timeout=45)
            if resp.status_code == 200:
                ans = resp.json().get("response", "").strip()
                if ans:
                    return True, ans, f"Ollama ({chosen_model})"
        except Exception as e:
            log_warn(f"Ошибка вызова Ollama {chosen_model}: {e}")

        return False, "", "Ollama: Ошибка инференса или отсутствует модель"

    # -------------------------------------------------------------------------
    # Fallback Orchestrator
    # -------------------------------------------------------------------------
    def analyze_screen(self, custom_prompt: str = None, image_input=None, user_prompt: str = None) -> tuple[bool, str, str]:
        """
        Executes the vision analysis through the fallback pipeline:
        Gemini -> OpenRouter Free -> OpenCode -> Ollama -> Graceful Fallback.
        Optionally accepts image_input (filepath str or PIL.Image) to analyze specific screenshots.
        Returns: (success: bool, text_response: str, provider_model: str)
        """
        effective_prompt = user_prompt if user_prompt is not None else custom_prompt
        if effective_prompt:
            prompt = (
                f"{DEFAULT_VISION_PROMPT}\n\n"
                f"Пользователь обращается к тебе с экраном: «{effective_prompt}».\n"
                f"Внимательно изучи прикреплённый снимок экрана и ответь на его слова, "
                f"описывая открытые окна, программы или происходящее на экране в своём неповторимом стиле Аластора (2-4 предложения)."
            )
        else:
            prompt = DEFAULT_VISION_PROMPT

        log_ai("Инициация захвата экрана и демонического зрения...")
        try:
            if image_input is not None:
                if isinstance(image_input, str):
                    img = Image.open(image_input)
                else:
                    img = image_input
                if img.mode != "RGB":
                    img = img.convert("RGB")
                w, h = img.size
                if max(w, h) > 1024:
                    scale = 1024 / float(max(w, h))
                    img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85)
                b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")
            else:
                _, b64_img, _ = self.take_screenshot()
        except Exception as e:
            log_error(f"Критическая ошибка захвата экрана: {e}")
            return (
                False,
                "Ха-ха! Помехи в эфире настолько сильны, что мой оптический взор затуманен! Не удалось захватить кадр экрана. 📺",
                "ScreenCaptureError"
            )

        gemini_key = self.config.get("gemini_api_key", "").strip()
        openrouter_key = self.config.get("openrouter_api_key", "").strip()
        opencode_key = self.config.get("opencode_api_key", "").strip()
        opencode_url = self.config.get("opencode_base_url", "https://api.opencode.ai/v1").strip()
        ollama_url = self.config.get("ollama_url", "http://localhost:11434").strip()

        errors = []

        # 1. Tier 1: Gemini Vision
        if gemini_key:
            ok, text, prov = self._call_gemini(b64_img, prompt, gemini_key)
            if ok:
                log_ai(f"Успешный анализ зрения через {prov}")
                return True, text, prov
            errors.append(prov)
        else:
            errors.append("Gemini (пропущен: нет ключа)")

        # 2. Tier 2: OpenRouter Free Models
        ok, text, prov = self._call_openrouter(b64_img, prompt, openrouter_key)
        if ok:
            log_ai(f"Успешный анализ зрения через {prov}")
            return True, text, prov
        errors.append(prov)

        # 3. Tier 3: OpenCode Vision
        ok, text, prov = self._call_opencode(b64_img, prompt, opencode_key, opencode_url)
        if ok:
            log_ai(f"Успешный анализ зрения через {prov}")
            return True, text, prov
        errors.append(prov)

        # 4. Tier 4: Ollama Local Vision
        ok, text, prov = self._call_ollama(b64_img, prompt, ollama_url)
        if ok:
            log_ai(f"Успешный анализ зрения через {prov}")
            return True, text, prov
        errors.append(prov)

        # 5. Fallback Response
        fallback_msg = (
            "Ха-ха! Кажется, все радио-линзы перекрыты помехами! 📻\n\n"
            "Ни один из провайдеров зрения не ответил:\n"
            + "\n".join(f"• {e}" for e in errors)
            + "\n\n💡 Укажи ключ Gemini или OpenRouter в настройках, либо запусти локальную Ollama с моделью llama3.2-vision!"
        )
        log_warn("Все провайдеры зрения завершились неудачей")
        return False, fallback_msg, "FallbackFailed"
