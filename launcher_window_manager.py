# -*- coding: utf-8 -*-
# window_manager.py - Window Management
import win32gui
import win32ui
import cv2
import numpy as np
from ctypes import windll
from launcher_config import BotConfig
import time

class WindowManager:
    def __init__(self):
        self.fivem_window = None
        
    def find_fivem_window(self):
        """ค้นหาหน้าต่าง FiveM แบบแม่นยำ"""
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if BotConfig.FIVEM_WINDOW_TITLE in title:
                    self.fivem_window = hwnd
            return True

        self.fivem_window = None
        win32gui.EnumWindows(callback, None)
        
        if self.fivem_window:
            rect = win32gui.GetWindowRect(self.fivem_window)
            if rect[2] - rect[0] > 100 and rect[3] - rect[1] > 100:
                return True
        
        return False
    
    def capture_fivem_screen(self):
        """จับภาพหน้าจอ FiveM แม้อยู่เบื้องหลัง"""
        if not self.fivem_window:
            time.sleep(1)
            return None
            
        try:
            hwnd = self.fivem_window
            rect = win32gui.GetWindowRect(hwnd)
            x, y, x2, y2 = rect
            width = x2 - x
            height = y2 - y
            
            # Create a memory device context (DC) for the screen capture
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # Create a bitmap to hold the captured image
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # Use PrintWindow to capture the window
            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)
            
            if result == 1:
                bmpstr = saveBitMap.GetBitmapBits(True)
                
                im = np.frombuffer(bmpstr, dtype='uint8')
                im.shape = (height, width, 4)
                
                opencv_image = cv2.cvtColor(im, cv2.COLOR_BGRA2BGR)
                
                # Clean up resources
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwndDC)
                
                self.last_screenshot = opencv_image
                return opencv_image
            else:
                return None
                
        except Exception as e:
            return None
    
    def get_window_handle(self):
        """ส่งคืน window handle"""
        return self.fivem_window