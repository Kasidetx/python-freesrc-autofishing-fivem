# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['c:\\Users\\openz\\Downloads\\botfish_v1\\pyarmor_dist\\autoupdate.py'],
    pathex=[],
    binaries=[],
    datas=[('c:\\Users\\openz\\Downloads\\botfish_v1\\assets', 'assets')],
    hiddenimports=['__pyarmor__', 'concurrent.futures', 'concurrent.futures.ThreadPoolExecutor', 'config', 'config.API_CONFIG', 'config.APP_CONFIG', 'ctypes', 'ctypes.windll', 'cv2', 'dataclasses', 'dataclasses.dataclass', 'hardware_id', 'hardware_id.HardwareIDGenerator', 'hashlib', 'inspect', 'keyboard', 'launcher_config', 'launcher_config.BotConfig', 'launcher_config.resource_path', 'launcher_game_detection_gui', 'launcher_game_detection_gui.GameDetectionGUI', 'launcher_gui_interface', 'launcher_gui_interface.GUIInterface', 'launcher_key_detector', 'launcher_key_detector.KeyDetector', 'launcher_key_executor', 'launcher_key_executor.KeyExecutor', 'launcher_launcher', 'launcher_launcher.FiveMFishingBotLauncher', 'launcher_main', 'launcher_main.FiveMFishingBot', 'launcher_template_manager', 'launcher_template_manager.TemplateManager', 'launcher_window_manager', 'launcher_window_manager.WindowManager', 'license_api', 'license_api.LicenseAPIClient', 'license_gui', 'license_gui.LicenseActivationGUI', 'main', 'main.LicenseManager', 'numpy', 'os', 'pathlib', 'pathlib.Path', 'platform', 'psutil', 'random', 're', 'requests', 'secrets', 'shutil', 'subprocess', 'sys', 'threading', 'time', 'tkinter', 'tkinter.messagebox', 'tkinter.ttk', 'typing', 'typing.Any', 'typing.Callable', 'typing.Dict', 'typing.List', 'typing.Optional', 'typing.Tuple', 'uuid', 'win32con', 'win32gui', 'win32ui', 'wmi'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='autoupdate_obfuscated',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['c:\\Users\\openz\\Downloads\\botfish_v1\\assets\\icon.ico'],
)
