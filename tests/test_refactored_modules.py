import os
import sys
import unittest

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from engine.physics import MascotPhysics
from engine.command_router import CommandRouter
from engine.autonomy import AutonomyManager
from engine.actions import MascotActions
from engine.context_menu import MascotContextMenu
from voice.dsp_profiles import DSP_PROFILES
from voice.tts_presets import VOICE_PRESETS, DEFAULT_SETTINGS
from windows.deal_manager import DealManager
from windows.aimp_controller import AIMPController
from windows.timer_manager import TimerManager
from windows.workspace_presets import WorkspacePresets
from ai.context_assistant import ContextAssistant


class MockInput:
    def click(self): return True
    def double_click(self): return True
    def right_click(self): return True
    def scroll(self, delta): return True
    def press_key(self, key): return True
    def hotkey(self, *k): return True
    def type_text(self, t): return True
    def playful_wiggle(self): return True
    def move_to_center(self): return True

class MockVolume:
    def __init__(self):
        self.vol = 50
        self.ducking_enabled = True
        self._duck_depth = 0
        self._pre_duck = None

    def set_volume(self, v, update_pre_duck=True):
        self.vol = v
        return v

    def get_volume(self): return self.vol
    def mute(self): return True
    def unmute(self): return True
    def toggle_mute(self): return True

    def start_ducking(self, target=15):
        if not self.ducking_enabled: return
        if self._duck_depth == 0:
            self._pre_duck = self.vol
            self.vol = target
        self._duck_depth += 1

    def stop_ducking(self):
        if not self.ducking_enabled: return
        if self._duck_depth > 0:
            self._duck_depth -= 1
            if self._duck_depth == 0 and self._pre_duck is not None:
                self.vol = self._pre_duck
                self._pre_duck = None

    def is_ducked(self): return self._duck_depth > 0

class MockSurface:
    def get_foreground_window(self): return None
    def get_open_windows(self): return []

class MockRoot:
    def after(self, ms, func, *args):
        try:
            func(*args)
        except Exception:
            pass

class MockVision:
    def analyze_screen(self, user_prompt=None):
        return True, "Анализ завершён", "mock"

class MockMascot:
    def __init__(self):
        self.sw = 1920
        self.sh = 1080
        self.is_muted = False
        self.surface_detector = MockSurface()
        self.physics_engine = MascotPhysics(self.sw, self.sh)
        self.autonomy_mgr = AutonomyManager(self)
        self.actions = MascotActions(self)
        self.input_ctrl = MockInput()
        self.volume_ctrl = MockVolume()
        self.vision_engine = MockVision()
        self.root = MockRoot()
        self.chat_win = None
        self.auto_capture_enabled = True
        self.spoken = []

        self.deal_mgr = DealManager(self)
        self.aimp_ctrl = AIMPController(self)
        self.context_asst = ContextAssistant(self)
        self.timer_mgr = TimerManager(self)
        self.workspace_presets = WorkspacePresets(self)

    @property
    def walk_on_windows_enabled(self): return self.physics_engine.walk_on_windows_enabled
    @walk_on_windows_enabled.setter
    def walk_on_windows_enabled(self, val): self.physics_engine.walk_on_windows_enabled = val

    def show_speech(self, text, play_audio=True):
        self.spoken.append(text)

    def set_mute(self, val):
        self.is_muted = val

    def set_auto_capture(self, val):
        self.auto_capture_enabled = val

    def toggle_auto_capture(self):
        self.auto_capture_enabled = not self.auto_capture_enabled

    def toggle_visibility(self):
        pass

    def action_jump_to_window(self):
        self.actions.jump_to_window()

    def action_jump_to_floor(self):
        self.actions.jump_to_floor()


class TestModularArchitecture(unittest.TestCase):
    def setUp(self):
        self.m = MockMascot()
        self.router = CommandRouter(self.m)

    def test_dsp_and_voice_presets(self):
        self.assertIn("canon_radio", DSP_PROFILES)
        self.assertIn("alastor_canon", VOICE_PRESETS)
        self.assertEqual(DEFAULT_SETTINGS["voice"], "ru-RU-DmitryNeural")

    def test_command_router_volume(self):
        handled, reply = self.router.route_command("громкость 80")
        self.assertTrue(handled)
        self.assertIn("80%", reply)

        handled, reply = self.router.route_command("потише")
        self.assertTrue(handled)
        self.assertIn("70%", reply)

    def test_command_router_window_walking(self):
        handled, reply = self.router.route_command("запрыгни на окно")
        self.assertTrue(handled)
        self.assertIn("Запрыгиваю", reply)

        handled, reply = self.router.route_command("спустись на пол")
        self.assertTrue(handled)
        self.assertIn("Спрыгиваю", reply)

        handled, reply = self.router.route_command("не ходи по окнам")
        self.assertTrue(handled)
        self.assertFalse(self.m.walk_on_windows_enabled)

    def test_command_router_input(self):
        handled, reply = self.router.route_command("двойной клик")
        self.assertTrue(handled)

        handled, reply = self.router.route_command("напечатай Hello World")
        self.assertTrue(handled)
        self.assertIn("Hello World", reply)

    def test_physics_engine(self):
        physics = self.m.physics_engine
        physics.set_state("walking")
        self.assertEqual(physics.state, "walking")
        self.assertNotEqual(physics.vel_x, 0)

        physics.set_state("falling")
        physics.y = 100
        physics.update_physics()
        self.assertGreater(physics.gravity, 0)

    def test_physics_ceiling_and_wall_orientation(self):
        physics = self.m.physics_engine

        # Test climb_left: upright (rotation 0), not flipped (hands reach left wall)
        physics.set_state("climb_left")
        self.assertEqual(physics.rotation, 0)
        self.assertFalse(physics.flipped)
        self.assertLess(physics.vel_y, 0)

        # Test climb_right: upright (rotation 0), flipped (hands reach right wall)
        physics.set_state("climb_right")
        self.assertEqual(physics.rotation, 0)
        self.assertTrue(physics.flipped)
        self.assertLess(physics.vel_y, 0)

        # Test ceiling walk: rotation is 180, flipped is inverted to prevent moonwalk
        physics.vel_x = 2  # moving right on ceiling
        physics.set_state("ceiling_walk")
        self.assertEqual(physics.rotation, 180)
        self.assertFalse(physics.flipped)  # facing right when rotated 180

        physics.vel_x = -2  # moving left on ceiling
        physics.set_state("ceiling_walk")
        self.assertEqual(physics.rotation, 180)
        self.assertTrue(physics.flipped)  # facing left when rotated 180

    def tearDown(self):
        if hasattr(self.m, 'deal_mgr') and self.m.deal_mgr.is_active:
            self.m.deal_mgr.cancel_deal()
        if hasattr(self.m, 'timer_mgr'):
            self.m.timer_mgr.stop()

    def test_command_router_auto_capture(self):
        handled, reply = self.router.route_command("выключи автозахват")
        self.assertTrue(handled)
        self.assertFalse(self.m.auto_capture_enabled)
        self.assertIn("отключён", reply)

        handled, reply = self.router.route_command("включи автозахват")
        self.assertTrue(handled)
        self.assertTrue(self.m.auto_capture_enabled)
        self.assertIn("активирован", reply)

    def test_deal_manager(self):
        deal = self.m.deal_mgr
        self.assertFalse(deal.is_active)
        res = deal.start_deal(25, "Тестовая задача")
        self.assertTrue(deal.is_active)
        self.assertEqual(deal.duration_minutes, 25)
        self.assertIn("25", res)

        # Duplicate deal attempt
        res_dup = deal.start_deal(10)
        self.assertIn("уже заключена", res_dup)

        # Status check
        status = deal.get_status()
        self.assertIn("Осталось", status)

        # Cancel deal
        res_cancel = deal.cancel_deal()
        self.assertFalse(deal.is_active)
        self.assertIn("расторгнута", res_cancel)

    def test_aimp_controller(self):
        aimp = self.m.aimp_ctrl
        self.assertEqual(aimp.WM_AIMP_COMMAND, 0x0475)
        self.assertEqual(aimp.CMD_PLAY, 13)
        self.assertEqual(aimp.CMD_PAUSE, 12)
        self.assertEqual(aimp.CMD_STOP, 11)
        self.assertEqual(aimp.CMD_NEXT, 16)
        self.assertEqual(aimp.CMD_PREV, 15)

        # Method safety check
        track = aimp.get_current_track()
        self.assertIsInstance(track, str)

    def test_timer_manager(self):
        tm = self.m.timer_mgr
        res = tm.add_timer(60, "проверить почту")
        self.assertIn("1 мин", res)
        self.assertIn("проверить почту", res)

        summary = tm.get_active_summary()
        self.assertIn("проверить почту", summary)

        # Natural language parsing: reminder
        handled, reply = tm.try_parse_and_schedule("напомни через 10 минут выключить плиту")
        self.assertTrue(handled)
        self.assertIn("10 мин", reply)

        # Natural language parsing: seconds timer
        handled, reply = tm.try_parse_and_schedule("таймер на 45 секунд")
        self.assertTrue(handled)
        self.assertIn("45 сек", reply)

        # Natural language parsing: cancel
        handled, reply = tm.try_parse_and_schedule("отмени таймеры")
        self.assertTrue(handled)
        self.assertIn("Сбросил", reply)
        self.assertEqual(len(tm.timers), 0)

    def test_workspace_presets(self):
        wp = self.m.workspace_presets
        handled, reply = wp.apply_preset("рабочий сетап")
        self.assertTrue(handled)
        self.assertIn("VS Code", reply)

        handled, reply = wp.apply_preset("игровой сетап")
        self.assertTrue(handled)
        self.assertIn("Steam", reply)

        handled, reply = wp.apply_preset("чистый стол")
        self.assertTrue(handled)
        self.assertIn("Свернул", reply)

        handled, reply = wp.apply_preset("неизвестный пресет")
        self.assertFalse(handled)

    def test_context_assistant(self):
        ca = self.m.context_asst
        info = ca.get_foreground_info()
        self.assertIn("hwnd", info)
        self.assertIn("title", info)
        self.assertIn("process", info)
        self.assertIn("category", info)

        # Method safety check
        ca.explain_active_error()
        ca.summarize_active_screen()

    def test_command_router_new_features(self):
        # 1. Deal commands
        handled, reply = self.router.route_command("сделка на 30 минут")
        self.assertTrue(handled)
        self.assertIn("30", reply)

        handled, reply = self.router.route_command("статус сделки")
        self.assertTrue(handled)

        handled, reply = self.router.route_command("отмени сделку")
        self.assertTrue(handled)

        # 2. AIMP commands
        handled, reply = self.router.route_command("включи радио")
        self.assertTrue(handled)

        handled, reply = self.router.route_command("следующий трек")
        self.assertTrue(handled)

        # 3. Context assistant commands
        handled, reply = self.router.route_command("помоги с кодом")
        self.assertTrue(handled)
        self.assertTrue(any("исходники" in s for s in self.m.spoken))

        handled, reply = self.router.route_command("кратко перескажи экран")
        self.assertTrue(handled)
        self.assertTrue(any("радио-фокус" in s for s in self.m.spoken))

        # 4. Timer commands
        handled, reply = self.router.route_command("таймер на 5 минут")
        self.assertTrue(handled)
        self.assertIn("5 мин", reply)

        # 5. Workspace presets
        handled, reply = self.router.route_command("рабочий сетап")
        self.assertTrue(handled)
        self.assertIn("VS Code", reply)

        # 6. Universal Music & Ducking commands
        handled, reply = self.router.route_command("пауза")
        self.assertTrue(handled)
        self.assertIn("пауз", reply)

        handled, reply = self.router.route_command("продолжи музыку")
        self.assertTrue(handled)

        handled, reply = self.router.route_command("скипни трек")
        self.assertTrue(handled)

        handled, reply = self.router.route_command("приглуши музыку")
        self.assertTrue(handled)
        self.assertIn("15%", reply)
        self.assertTrue(self.m.volume_ctrl.is_ducked())

        handled, reply = self.router.route_command("верни громкость")
        self.assertTrue(handled)
        self.assertFalse(self.m.volume_ctrl.is_ducked())

        handled, reply = self.router.route_command("включи приглушение")
        self.assertTrue(handled)
        self.assertTrue(self.m.volume_ctrl.ducking_enabled)

    def test_volume_controller_ducking(self):
        from windows.volume_controller import VolumeController
        vc = VolumeController()
        if not vc.is_available():
            return
        orig = vc.get_volume()
        try:
            vc.set_volume(50)
            self.assertEqual(vc.get_volume(), 50)
            vc.start_ducking(15)
            self.assertTrue(vc.is_ducked())
            self.assertEqual(vc.get_volume(), 15)
            # Nested call
            vc.start_ducking(10)
            self.assertTrue(vc.is_ducked())
            vc.stop_ducking()
            self.assertTrue(vc.is_ducked())
            # Final release restores pre-duck volume
            vc.stop_ducking()
            self.assertFalse(vc.is_ducked())
            self.assertEqual(vc.get_volume(), 50)
        finally:
            vc.set_volume(orig)


if __name__ == "__main__":
    unittest.main()

