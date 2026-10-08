# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [
    ('img', 'img'),
    ('Actions.xml', '.'),
    ('Behaviors.xml', '.'),
    ('apps_config.json', '.'),
    ('voice_settings.json', '.'),
]

if os.path.exists('ai_config.json'):
    datas.append(('ai_config.json', '.'))
if os.path.exists('voice/audio_cache'):
    datas.append(('voice/audio_cache', 'voice/audio_cache'))

binaries = []
hiddenimports = [
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'pystray',
    'pystray._win32',
    'sounddevice',
    'soundfile',
    'scipy',
    'scipy.signal',
    'numpy',
    'pyautogui',
    'keyboard',
    'mss',
    'mss.windows',
    'requests',
    'edge_tts',
    'pedalboard',
    'comtypes',
    'pycaw',
    'pycaw.pycaw',
    'pycaw.constants',
    'pycaw.utils',
    'win32gui',
    'win32con',
    'win32api',
    'win32process',
    'win32clipboard',
    'winshell',
    'speech_recognition',
    'yt_dlp',
]

for pkg in ['_sounddevice_data', '_soundfile_data', 'pedalboard', 'ctranslate2', 'faster_whisper']:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

for mod in ['engine', 'windows', 'voice', 'ai', 'core']:
    hiddenimports += collect_submodules(mod)

a = Analysis(
    ['PinkChan.pyw'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'pandas', 'IPython', 'notebook', 'pytest', 'unittest'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Alastor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['img/icon.ico'],
)
