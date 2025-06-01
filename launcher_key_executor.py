# -*- coding: utf-8 -*-
# key_executor.py - Key Execution System (Fixed)
import ctypes
import time
import random
import win32gui
import win32con
from launcher_config import BotConfig

class KeyExecutor:
    def __init__(self):
        self.key_map = BotConfig.KEY_MAP
        self.reaction_delay = BotConfig.REACTION_DELAY
        
        # Initialize user32 functions
        self.user32 = ctypes.WinDLL('user32')
        self.user32.GetForegroundWindow.restype = ctypes.c_void_p
        self.user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
        self.user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.user32.IsIconic.argtypes = [ctypes.c_void_p]
        self.user32.SwitchToThisWindow.argtypes = [ctypes.c_void_p, ctypes.c_bool]
        
        self.kernel32 = ctypes.WinDLL('kernel32')
        self.kernel32.GetCurrentThreadId.restype = ctypes.c_int
        
    def set_foreground_window(self, hwnd):
        """Bring window to foreground with minimal disruption for background operations."""
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False

        try:
            # Restore window if minimized
            if self.user32.IsIconic(hwnd):
                self.user32.ShowWindow(hwnd, win32con.SW_RESTORE)
            else:
                self.user32.ShowWindow(hwnd, win32con.SW_SHOW)

            # Get thread IDs for input attachment
            current_thread = self.kernel32.GetCurrentThreadId()
            target_thread = self.user32.GetWindowThreadProcessId(hwnd, None)
            
            # Temporarily attach thread input
            self.user32.AttachThreadInput(current_thread, target_thread, True)
            
            # Combined focus approach
            self.user32.BringWindowToTop(hwnd)
            self.user32.SetForegroundWindow(hwnd)
            self.user32.SwitchToThisWindow(hwnd, True)  # Undocumented fallback
            
            # Verify focus success
            return self.user32.GetForegroundWindow() == hwnd
            
        except Exception as e:
            print(f"Set foreground error: {e}")
            return False
        finally:
            # Clean up thread attachment
            try:
                self.user32.AttachThreadInput(current_thread, target_thread, False)
            except:
                pass
    
    def execute_key_sequence(self, sequence, hwnd):
        """this is bug for send key to background fakefocus"""
        if not sequence:
            return False

        original_hwnd = None
        try:
            # Save original foreground window
            original_hwnd = self.user32.GetForegroundWindow()
            
            # Force focus to target window
            self.set_foreground_window(hwnd)
            success_count = 0

            for i, key in enumerate(sequence):
                if key in self.key_map:
                    # Check and maintain window focus before each key
                    if self.user32.GetForegroundWindow() != hwnd:
                        self.set_foreground_window(hwnd)
                    
                    # Execute key press
                    mapped_key = self.key_map[key]
                    key_success = self.send_key_to_window(hwnd, mapped_key)
                    if key_success:
                        success_count += 1

                    # Add reaction delay
                    if i < len(sequence) - 1:
                        time.sleep(self.reaction_delay)
                else:
                    continue

            time.sleep(0.1)
            return success_count > 0

        except Exception as e:
            print(f"Key execution error: {e}")
            return False
        finally:
            # Restore original focus
            if original_hwnd and win32gui.IsWindow(original_hwnd):
                self.set_foreground_window(original_hwnd)

    def send_key_to_window(self, hwnd, key):
        """Enhanced key sending with thread attachment"""
        try:
            if not hwnd or not win32gui.IsWindow(hwnd):
                return False

            vk_code, scan_code = BotConfig.VK_MAP.get(key.lower(), (None, None))
            if not vk_code:
                return False

            lparam_down = (scan_code << 16) | 1
            lparam_up = (scan_code << 16) | 0xC0000001

            # Method 1: PostMessage
            result1 = self.user32.PostMessageW(hwnd, BotConfig.WM_KEYDOWN, vk_code, lparam_down)
            time.sleep(0.01)
            result2 = self.user32.PostMessageW(hwnd, BotConfig.WM_KEYUP, vk_code, lparam_up)

            time.sleep(random.uniform(0.02, 0.05))
            return (result1 != 0 and result2 != 0)

        except Exception as e:
            print(f"Send key error: {e}")
            return False