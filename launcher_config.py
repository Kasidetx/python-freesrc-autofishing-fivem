# config.py - Configuration Settings
import os
import sys

def resource_path(relative_path):
    """ คืน path ที่ถูกต้องทั้งตอนรัน .py และ .exe """
    try:
        base_path = sys._MEIPASS  # ถูกใช้โดย PyInstaller ตอนรัน .exe
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Bot Configuration
class BotConfig:
    # Key mappings for minigame
    KEY_MAP = { 'W':'w','A':'a','S':'s','D':'d' }

    # แค่เก็บชื่อไฟล์ไว้
    TEMPLATE_FILES = ["W.png","A.png","S.png","D.png"]

    @classmethod
    def get_template_paths(cls):
        """
        คืนลิสต์ path เต็ม ๆ ของไฟล์ใน assets/
        """
        return [
            resource_path(os.path.join('assets', fname))
            for fname in cls.TEMPLATE_FILES
        ]

    
    # Detection settings
    TARGET_SEQUENCE_LENGTH = 5
    SEQUENCE_STABLE_TIME = 0.3
    SENSITIVITY = 0.8
    REACTION_DELAY = 0.01
    MIN_CONSECUTIVE_DETECTIONS = 3
    MIN_DISTANCE = 20
    
    # Window settings
    FIVEM_WINDOW_TITLE = "FiveM® by Cfx.re - COMMU6"
    
    DEBUG_MODE = False
    
    # Virtual Key Codes
    VK_MAP = {
        'w': (0x57, 0x11),
        'a': (0x41, 0x1E),
        's': (0x53, 0x1F),
        'd': (0x44, 0x20)
    }
    
    # Windows Messages
    WM_KEYDOWN = 0x100
    WM_KEYUP = 0x101