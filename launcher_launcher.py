# -*- coding: utf-8 -*-
# launcher.py - Main Entry Point with Game Detection
import sys
from launcher_game_detection_gui import GameDetectionGUI
from launcher_main import FiveMFishingBot

class FiveMFishingBotLauncher:
    def __init__(self):
        self.fivem_hwnd = None
        self.main_bot = None
        
    def on_game_detected(self, hwnd):
        self.fivem_hwnd = hwnd
        
        self.main_bot = FiveMFishingBot(
            detected_hwnd=hwnd, 
        )
        
        self.main_bot.run()
    
    def run(self):
        
        try:
            detection_gui = GameDetectionGUI(self.on_game_detected)
            detection_gui.run()
        except Exception as e:
            print(f"Failed to start game detection: {e}")
            sys.exit(1)