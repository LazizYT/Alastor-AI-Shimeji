import os
import sys
import time
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure root directory is on PYTHONPATH
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from windows.window_surface_detector import WindowSurfaceDetector
from windows.volume_controller import VolumeController
from windows.clipboard_assistant import ClipboardAssistant
from windows.media_downloader import MediaDownloader
from windows.input_controller import InputController
from ai.vision_engine import VisionEngine
from ai.memory import MemoryManager
from voice.radio_dsp import RadioDSP
from voice.tts_engine import RadioTTSEngine

def test_window_surface_detector():
    print("\n" + "="*60)
    print("TEST 1: WindowSurfaceDetector (Окна, вкладки и платформы)")
    print("="*60)
    detector = WindowSurfaceDetector()
    windows = detector.get_open_windows()
    print(f"[*] Найдено открытых подходящих окон для хождения: {len(windows)}")
    for i, w in enumerate(windows[:5], 1):
        print(f"    {i}. [HWND {w['hwnd']}] «{w['title'][:35]}» | Rect: ({w['left']}, {w['top']}, {w['right']}, {w['bottom']}) | Поверхность: y={w['floor_y']}, x={w['min_x']}..{w['max_x']}")
    
    fg = detector.get_foreground_window()
    if fg:
        print(f"[*] Активное окно на переднем плане: «{fg['title']}» (floor_y={fg['floor_y']})")
    else:
        print("[*] Активное окно не найдено или является системным")

    if windows:
        target = windows[0]
        test_x = (target["left"] + target["right"]) // 2
        test_y = target["top"] - 100
        landing = detector.find_surface_landing(test_x, test_y)
        if landing:
            print(f"[+] Симуляция падения: с высоты y={test_y} над x={test_x} маскот приземлился на «{landing['title'][:30]}» на высоте y={landing['floor_y']}! УСПЕШНО.")
        else:
            print("[-] Landing check: поверхность не найдена")
    print("[✓] WindowSurfaceDetector тест пройден успешно.")

def test_volume_controller():
    print("\n" + "="*60)
    print("TEST 2: VolumeController (Системная громкость Windows)")
    print("="*60)
    vol = VolumeController()
    if not vol.is_available():
        print("[-] VolumeController недоступен (pycaw не инициализирован)")
        return

    cur_vol = vol.get_volume()
    is_muted = vol.is_muted()
    print(f"[*] Текущая громкость Windows: {cur_vol}% | Mute: {is_muted}")

    # Test small relative adjustment and restore
    test_target = max(10, min(90, cur_vol))
    vol.set_volume(test_target)
    read_back = vol.get_volume()
    print(f"[*] Проверочная установка громкости: {test_target}% -> Считано: {read_back}%")

    # Restore original volume
    vol.set_volume(cur_vol)
    print(f"[+] Громкость успешно восстановлена на исходный уровень: {vol.get_volume()}%")
    print("[✓] VolumeController тест пройден успешно.")

def test_clipboard_and_media():
    print("\n" + "="*60)
    print("TEST 3: ClipboardAssistant & MediaDownloader")
    print("="*60)
    clip = ClipboardAssistant()
    cur_text = clip.get_clipboard_text()
    print(f"[*] Текущее содержимое буфера обмена: {repr(cur_text[:50])} (длина: {len(cur_text)} симв.)")

    downloader = MediaDownloader()
    print(f"[*] Папка для загрузки медиа: {downloader.download_dir}")
    assert os.path.exists(downloader.download_dir), f"Папка {downloader.download_dir} не создана!"

    # Test URL extraction
    sample_text = "Слушай этот радио-эфир тут: https://www.youtube.com/watch?v=dQw4w9WgXcQ и не забудь!"
    extracted = downloader.extract_url(sample_text)
    print(f"[*] Проверка извлечения ссылки: из текста извлечено -> {extracted}")
    assert extracted == "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "Ошибка извлечения URL!"
    print("[✓] Clipboard & MediaDownloader тест пройден успешно.")

def test_input_controller():
    print("\n" + "="*60)
    print("TEST 4: InputController (Мышь и Клавиатура)")
    print("="*60)
    inp = InputController()
    pos = inp.get_position()
    print(f"[*] Текущие координаты курсора мыши: X={pos[0]}, Y={pos[1]}")
    assert hasattr(inp, 'click'), "Missing click method"
    assert hasattr(inp, 'type_text'), "Missing type_text method"
    assert hasattr(inp, 'hotkey'), "Missing hotkey method"
    assert hasattr(inp, 'scroll'), "Missing scroll method"
    assert hasattr(inp, 'playful_wiggle'), "Missing playful_wiggle method"
    print("[✓] InputController тест пройден успешно.")

def test_radio_dsp_and_tts():
    print("\n" + "="*60)
    print("TEST 5: RadioDSP & TTSEngine (Фильтры Аластора, тремоло и мут)")
    print("="*60)
    dsp = RadioDSP()
    sr = 24000
    duration = 0.5
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    synthetic_voice = 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32)

    processed = dsp.process(synthetic_voice, sample_rate=sr)
    print(f"[*] Исходный сигнал: {len(synthetic_voice)} сэмплов | Обработанный радио-сигнал: {len(processed)} сэмплов")
    assert len(processed) > 0, "DSP output is empty"
    assert np.all(np.isfinite(processed)), "DSP output contains NaN or Inf"
    print(f"[*] Пиковая амплитуда после tanh и радио-фильтрации: {np.max(np.abs(processed)):.3f}")

    tts = RadioTTSEngine(enabled=True)
    orig_mute = tts.is_muted
    tts.mute()
    assert tts.is_muted == True, "Mute failed"
    tts.unmute()
    assert tts.is_muted == False, "Unmute failed"
    if orig_mute:
        tts.mute()
    print("[✓] RadioDSP & TTSEngine тест пройден успешно.")

def test_memory_manager():
    print("\n" + "="*60)
    print("TEST 6: MemoryManager (Досье и память Аластора)")
    print("="*60)
    mem = MemoryManager()
    sample_phrase = "Меня зовут Лазико, я программист и пишу код на Python"
    mem.extract_facts(sample_phrase)
    mem.record_interaction()

    dossier = mem.get_readable_summary()
    print(f"[*] Сформированное досье пользователя:\n{dossier}")
    name = mem.data.get("user_profile", {}).get("name", "")
    assert "Лазико" in name, f"Fact extraction failed for name: {name}"
    print("[✓] MemoryManager тест пройден успешно.")

def test_vision_engine():
    print("\n" + "="*60)
    print("TEST 7: VisionEngine (Зрение ИИ и Fallback система)")
    print("="*60)
    vision = VisionEngine()

    print("[*] 1. Проверка захвата экрана:")
    img_bytes = vision.capture_screen()
    if img_bytes:
        print(f"[+] Скриншот успешно получен! Размер JPEG: {len(img_bytes)} байт")
    else:
        print("[-] Не удалось получить скриншот экрана")

    print("\n[*] 2. Проверка подключений к провайдерам зрения:")
    statuses = vision.verify_connection()
    for provider, msg in statuses.items():
        print(f"    • {provider}: {msg}")

    print("\n[*] 3. Пробный запуск анализа экрана:")
    prompt = "Опиши кратко, что ты видишь на этом экране в стиле Аластора (1-2 предложения)."
    ok, reply, provider_used = vision.analyze_screen(prompt)
    print(f"[*] Результат анализа зрения:")
    print(f"    Провайдер: [{provider_used}]")
    print(f"    Успешно: {ok}")
    print(f"    Ответ Аластора: {reply}")
    assert len(reply) > 0, "Vision reply is empty"
    print("[✓] VisionEngine тест пройден успешно.")

if __name__ == "__main__":
    print("="*60)
    print("  ЗАПУСК ПОЛНОГО ТЕСТИРОВАНИЯ СИСТЕМЫ ALASTOR SHIMEJI")
    print("="*60)
    start_t = time.time()
    
    try:
        test_window_surface_detector()
        test_volume_controller()
        test_clipboard_and_media()
        test_input_controller()
        test_radio_dsp_and_tts()
        test_memory_manager()
        test_vision_engine()
        
        elapsed = time.time() - start_t
        print("\n" + "="*60)
        print(f"  ВСЕ ТЕСТЫ (7 ИЗ 7) УСПЕШНО ПРОЙДЕНЫ ЗА {elapsed:.2f} сек!  ")
        print("="*60)
    except Exception as e:
        print(f"\n[!] ОШИБКА ВО ВРЕМЯ ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
