"""
Preset profiles for vintage radio, studio microphones, and Alastor demonic audio effects.
"""

DSP_PROFILES = {
    "canon_radio": {
        "title": "📻 Каноничный Аластор (Радио 1930-х)",
        "category": "radio",
        "highpass_hz": 350.0,
        "lowpass_hz": 3800.0,
        "drive_db": 6.0,
        "add_vinyl": True,
        "vinyl_intensity": 1.0,
        "demon_layer": True,
        "chain_type": "radio"
    },
    "gramophone": {
        "title": "📻 Старый патефон / Граммофон (1920-е)",
        "category": "radio",
        "highpass_hz": 480.0,
        "lowpass_hz": 2600.0,
        "drive_db": 10.0,
        "add_vinyl": True,
        "vinyl_intensity": 2.2,
        "demon_layer": True,
        "chain_type": "radio"
    },
    "am_radio": {
        "title": "📻 Коротковолновый эфир (Шумный AM)",
        "category": "radio",
        "highpass_hz": 420.0,
        "lowpass_hz": 3100.0,
        "drive_db": 8.0,
        "add_vinyl": True,
        "vinyl_intensity": 1.6,
        "demon_layer": True,
        "chain_type": "radio"
    },
    "walkie_talkie": {
        "title": "📻 Рация Walkie-Talkie (Резкий эфир)",
        "category": "radio",
        "highpass_hz": 500.0,
        "lowpass_hz": 3000.0,
        "drive_db": 10.0,
        "add_vinyl": False,
        "vinyl_intensity": 0.0,
        "demon_layer": False,
        "chain_type": "walkie"
    },
    "telephone": {
        "title": "📞 Телефонная линия (1960-е)",
        "category": "radio",
        "highpass_hz": 400.0,
        "lowpass_hz": 2800.0,
        "drive_db": 4.0,
        "add_vinyl": False,
        "vinyl_intensity": 0.0,
        "demon_layer": False,
        "chain_type": "telephone"
    },
    "megaphone": {
        "title": "📢 Мегафон / Уличный рупор",
        "category": "radio",
        "highpass_hz": 600.0,
        "lowpass_hz": 3500.0,
        "drive_db": 14.0,
        "add_vinyl": False,
        "vinyl_intensity": 0.0,
        "demon_layer": False,
        "chain_type": "megaphone"
    },
    "demon_radio": {
        "title": "😈 Демонический эфир Аластора (Dark Overlord)",
        "category": "radio",
        "highpass_hz": 180.0,
        "lowpass_hz": 4500.0,
        "drive_db": 12.0,
        "add_vinyl": True,
        "vinyl_intensity": 0.8,
        "demon_layer": True,
        "chain_type": "demon"
    },
    "shadow_realm": {
        "title": "🏛️ Театр теней / Эхо Преисподней",
        "category": "radio",
        "highpass_hz": 250.0,
        "lowpass_hz": 5200.0,
        "drive_db": 5.0,
        "add_vinyl": True,
        "vinyl_intensity": 0.5,
        "demon_layer": True,
        "chain_type": "shadow"
    },
    "studio_warm": {
        "title": "🎙️ Тёплый студийный микрофон (Подкаст)",
        "category": "normal",
        "highpass_hz": 80.0,
        "lowpass_hz": 12000.0,
        "drive_db": 0.0,
        "add_vinyl": False,
        "vinyl_intensity": 0.0,
        "demon_layer": False,
        "chain_type": "studio_warm"
    },
    "studio_crystal": {
        "title": "🎙️ Кристальная студия (High-End)",
        "category": "normal",
        "highpass_hz": 60.0,
        "lowpass_hz": 16000.0,
        "drive_db": 0.0,
        "add_vinyl": False,
        "vinyl_intensity": 0.0,
        "demon_layer": False,
        "chain_type": "studio_crystal"
    },
    "studio_latenight": {
        "title": "🎙️ Ночной радиоведущий (Глубокий бархат)",
        "category": "normal",
        "highpass_hz": 70.0,
        "lowpass_hz": 11000.0,
        "drive_db": 0.0,
        "add_vinyl": False,
        "vinyl_intensity": 0.0,
        "demon_layer": False,
        "chain_type": "studio_latenight"
    },
    "clean": {
        "title": "🎙️ Чистый звук (Bypass / Без эффектов)",
        "category": "normal",
        "highpass_hz": 50.0,
        "lowpass_hz": 18000.0,
        "drive_db": 0.0,
        "add_vinyl": False,
        "vinyl_intensity": 0.0,
        "demon_layer": False,
        "chain_type": "clean"
    }
}
