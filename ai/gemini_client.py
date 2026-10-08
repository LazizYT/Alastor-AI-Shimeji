from core.config import REQUESTS_AVAILABLE

if REQUESTS_AVAILABLE:
    import requests

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-1.5-flash",
    "gemini-pro"
]

def query_gemini(api_key: str, contents: list, system_prompt: str, max_tokens: int = 1024, temperature: float = 0.9, timeout: int = 40):
    if not api_key:
        raise ValueError("API-ключ Gemini не указан!")
    if not REQUESTS_AVAILABLE:
        raise RuntimeError("Библиотека requests не установлена!")

    last_err = None
    for model in GEMINI_MODELS:
        gen_config = {"temperature": temperature, "maxOutputTokens": max_tokens}
        if "2.5" in model:
            gen_config["thinkingConfig"] = {"thinkingBudget": 0}

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": gen_config
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 404:
                continue
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except requests.RequestException as e:
            last_err = e
            continue

    if last_err:
        raise last_err
    raise RuntimeError("Не удалось получить ответ ни от одной модели Gemini")

def verify_gemini_connection(api_key: str) -> tuple[bool, str]:
    if not api_key:
        return False, "Сначала укажите API-ключ Gemini!"
    if not REQUESTS_AVAILABLE:
        return False, "Отсутствует библиотека requests"

    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": "ping"}]}]}
        try:
            resp = requests.post(url, json=payload, timeout=6)
            if resp.status_code in (200, 400):
                return True, f"Подключение к Gemini API ({model}) успешно!"
        except Exception as e:
            return False, f"Ошибка подключения к API: {e}"

    return False, "Не удалось связаться с серверами Gemini API"
