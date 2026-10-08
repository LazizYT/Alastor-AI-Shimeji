import os
import json
import time
import re
import threading
from core.config import BASE_DIR
from core.logger import log_info

MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")
_LOCK = threading.Lock()

class MemoryManager:
    """
    Long-term and relational memory system for Alastor AI Shimeji companion.
    Persists user preferences, known facts, conversation summaries, and Alastor's deals.
    """
    def __init__(self):
        self.data = self._load()

    def _default_data(self) -> dict:
        return {
            "user_profile": {
                "name": "Друг",
                "role": "Владелец этого экрана",
                "facts": [],
                "interests": [],
                "favorite_apps": []
            },
            "alastor_relationship": {
                "first_met": time.strftime("%Y-%m-%d"),
                "total_interactions": 0,
                "deals_struck": [],
                "amusement_level": "Высокий"
            },
            "recent_topics": []
        }

    def _load(self) -> dict:
        with _LOCK:
            if not os.path.exists(MEMORY_FILE):
                data = self._default_data()
                self._save_raw(data)
                return data
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return self._default_data()

    def _save_raw(self, data: dict):
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def save(self):
        with _LOCK:
            self._save_raw(self.data)

    def record_interaction(self):
        with _LOCK:
            rel = self.data.setdefault("alastor_relationship", {})
            rel["total_interactions"] = rel.get("total_interactions", 0) + 1
        self.save()

    def add_fact(self, fact_text: str):
        fact = fact_text.strip()
        if not fact:
            return
        with _LOCK:
            facts = self.data.setdefault("user_profile", {}).setdefault("facts", [])
            if fact not in facts:
                facts.append(fact)
                log_info(f"Аластор запомнил факт о пользователе: {fact}")
        self.save()

    def set_user_name(self, name: str):
        clean_name = name.strip().capitalize()
        if clean_name:
            with _LOCK:
                self.data.setdefault("user_profile", {})["name"] = clean_name
                log_info(f"Аластор запомнил имя пользователя: {clean_name}")
            self.save()

    def strike_deal(self, terms: str):
        with _LOCK:
            deals = self.data.setdefault("alastor_relationship", {}).setdefault("deals_struck", [])
            deal_entry = {
                "date": time.strftime("%Y-%m-%d %H:%M"),
                "terms": terms
            }
            deals.append(deal_entry)
            log_info(f"Заключена сделка с Аластором: {terms}")
        self.save()

    def extract_facts(self, user_text: str):
        """Automatically detect names, preferences, and personal details from speech/chat."""
        low = user_text.lower().strip()

        # 1. Name detection
        name_m = re.search(r'(?:меня зовут|мо[её] имя|зови меня)\s+([А-Яа-яA-Za-z]+)', user_text, re.IGNORECASE)
        if name_m:
            found_name = name_m.group(1).strip()
            if len(found_name) > 1 and found_name.lower() not in ("аластор", "демон", "друг", "привет"):
                self.set_user_name(found_name)

        # 2. Likes / preferences
        like_m = re.search(r'(?:я люблю|мне нравится|я обожаю|мой любимый|моя любимая)\s+([^.!?,\n]+)', user_text, re.IGNORECASE)
        if like_m:
            interest = like_m.group(1).strip()
            if len(interest) > 2:
                self.add_fact(f"Любит: {interest}")

        # 3. Work / profession
        work_m = re.search(r'(?:я работаю|я учусь на|я по профессии|я)\s+(программист\w*|разработчик\w*|дизайнер\w*|художник\w*|студент\w*|инженер\w*)', user_text, re.IGNORECASE)
        if work_m:
            prof = work_m.group(1).strip()
            self.add_fact(f"Род деятельности: {prof}")

        # 4. Deals detection
        if any(w in low for w in ["договорились", "по рукам", "согласен на сделку", "заключаем сделку"]):
            self.strike_deal("Пользователь согласился на неопределённую дружескую услугу в будущем.")

    def get_prompt_context(self) -> str:
        """Generates contextual prompt snippet injected into LLM queries."""
        profile = self.data.get("user_profile", {})
        rel = self.data.get("alastor_relationship", {})

        name = profile.get("name", "Друг")
        facts = profile.get("facts", [])
        deals = rel.get("deals_struck", [])

        lines = [f"[ТВОЯ ПАМЯТЬ ОБ ЭТОМ ПОЛЬЗОВАТЕЛЕ]:"]
        lines.append(f"- Имя/обращение к собеседнику: {name}")
        if facts:
            lines.append(f"- Известные детали и привычки: {', '.join(facts[-5:])}")
        if deals:
            lines.append(f"- Заключенные сделки/долги: {len(deals)} соглашений (последнее: {deals[-1]['terms']})")
        lines.append("- Инструкция: Используй эти знания естественно, как внимательный и учтивый хозяин эфира!")

        return "\n".join(lines)

    def get_readable_summary(self) -> str:
        """Returns clean human-readable text for UI / speech bubble."""
        profile = self.data.get("user_profile", {})
        rel = self.data.get("alastor_relationship", {})

        name = profile.get("name", "Друг")
        facts = profile.get("facts", [])
        deals = rel.get("deals_struck", [])
        interactions = rel.get("total_interactions", 0)

        out = [f"📻 Досье Радио-демона:"]
        out.append(f"👤 Собеседник: {name}")
        out.append(f"🎙️ Взаимодействий в эфире: {interactions}")

        if facts:
            out.append("🧠 Память о вас:")
            for f in facts[-4:]:
                out.append(f"  • {f}")
        else:
            out.append("🧠 Память о вас: Пока собираю сведения...")

        if deals:
            out.append(f"🤝 Сделок заключено: {len(deals)}")

        return "\n".join(out)

    def clear_memory(self):
        with _LOCK:
            self.data = self._default_data()
        self.save()
        log_info("Память Аластора очищена пользователем")
