#!/usr/bin/env python3
"""
Pre-caches all standard Alastor phrases through Edge-TTS and Pedalboard DSP
into voice/audio_cache/ so that when Alastor speaks them in-game, there is 0ms delay!
"""

import os
import io
import re
import sys
import hashlib
import asyncio
import numpy as np

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import edge_tts
import soundfile as sf
from core.constants import SPEECHES, POKED_SPEECHES, CANON_ARCHIVE
from voice.radio_dsp import RadioDSP

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

EXTRA_PHRASES = [
    "Шоу в эфире! Слушаю вас, говорите в микрофон!",
    "Обрабатываю радиоволны, распознавание речи!",
    "Ха-ха! Тишина в эфире... Я ничего не услышал!",
    "Ввысь, к радиомачтам!",
    "Шоу расширяет границы!",
    "Этот экран теперь мой!",
    "Поймал! Перетаскивайте!",
    "Отпустил окно!",
    "Свернул окно! Отдыхай!",
    "Закрыл активное окно! Шоу окончено!",
    "Перемешал значки на рабочем столе!",
    "Разбросал значки!",
    "Выровнял по сетке!",
    "Навёл идеальный порядок на рабочем столе!",
    "Прибавил громкость! Да звучит музыка на полную!",
    "Сделал потише! Приглушим радиопомехи!",
    "Звук переключен! Тишина в эфире...",
    "Радио-голос включен!",
    "Радио-голос выключен!",
]

def sanitize_text(text: str) -> str:
    cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    cleaned = re.sub(r'\([^\)]*\)', '', cleaned)
    cleaned = re.sub(r'[*_#`~]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

async def generate_phrase(text: str, dsp: RadioDSP, voice="ru-RU-DmitryNeural", rate="+8%", pitch="+2Hz"):
    clean_text = sanitize_text(text)
    if not clean_text:
        return
    key = hashlib.md5(clean_text.encode('utf-8')).hexdigest()
    out_file = os.path.join(CACHE_DIR, f"{key}.wav")

    if os.path.exists(out_file):
        print(f"✓ Уже в кеше: «{clean_text[:40]}...»")
        return

    print(f"⏳ Генерация: «{clean_text[:40]}...»")
    try:
        communicate = edge_tts.Communicate(clean_text, voice, rate=rate, pitch=pitch)
        mp3_data = bytearray()
        async for chunk in communicate.stream():
            if chunk['type'] == 'audio':
                mp3_data.extend(chunk['data'])

        audio, sr = sf.read(io.BytesIO(mp3_data))
        processed = dsp.process(audio, sr, add_vinyl=True)
        sf.write(out_file, processed, sr)
        print(f"  -> Сохранено: {os.path.basename(out_file)}")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")

async def main():
    dsp = RadioDSP()
    all_phrases = []

    for s in SPEECHES:
        all_phrases.append(s)
    for p in POKED_SPEECHES:
        all_phrases.append(p)
    for cat, quotes in CANON_ARCHIVE.items():
        for q in quotes:
            all_phrases.append(q)
    for ext in EXTRA_PHRASES:
        all_phrases.append(ext)

    unique_phrases = list(dict.fromkeys(all_phrases))
    print(f"Всего уникальных фраз для пре-кеширования: {len(unique_phrases)}")

    for phrase in unique_phrases:
        await generate_phrase(phrase, dsp)

    print("\n🎉 Все существующие фразы Аластора предварительно сгенерированы и сохранены в кеш!")

if __name__ == "__main__":
    asyncio.run(main())
