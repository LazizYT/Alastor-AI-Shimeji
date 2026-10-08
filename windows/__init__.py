"""Windows OS integration modules (Window dragging, Desktop icons, Win32 Hotkeys, Log Viewer)."""
from windows.window_dragger import WindowDragger
from windows.desktop_icons import DesktopIconMover
from windows.hotkeys import HotkeyManager
from windows.log_viewer import LogViewerWindow
from windows.voice_settings import VoiceSettingsWindow
from windows.input_controller import InputController
from windows.tray_icon import TrayIconManager
from windows.volume_controller import VolumeController
from windows.media_downloader import MediaDownloader
from windows.clipboard_assistant import ClipboardAssistant
from windows.window_surface_detector import WindowSurfaceDetector

__all__ = [
    "WindowDragger", "DesktopIconMover", "HotkeyManager",
    "LogViewerWindow", "VoiceSettingsWindow", "InputController", "TrayIconManager",
    "VolumeController", "MediaDownloader", "ClipboardAssistant", "WindowSurfaceDetector"
]


