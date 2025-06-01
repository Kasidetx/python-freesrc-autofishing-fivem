# -*- coding: utf-8 -*-
# game_detection_gui.py - Game Detection GUI
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import win32gui
from launcher_config import BotConfig
import sys
from config import APP_CONFIG

class GameDetectionGUI:
    def __init__(self, on_game_detected_callback):
        self.on_game_detected = on_game_detected_callback
        self.is_detecting = True
        self.detection_thread = None
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("")
        icon_path = APP_CONFIG.get_icon_path()
        self.root.iconbitmap(icon_path)
        self.root.geometry("500x250")
        self.root.resizable(False, False)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (250 // 2)
        self.root.geometry(f"500x250+{x}+{y}")
        
        # Set window icon and properties
        self.root.configure(bg='#2b2b2b')
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.setup_ui()
        self.start_detection()
    
    def setup_ui(self):
        """สร้าง UI สำหรับการตรวจจับเกม"""
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Good Town - ตกปลา",
            font=("Arial", 18, "bold"),
            fg="#9900ff",
            bg='#2b2b2b'
        )
        title_label.pack(pady=(0, 20))
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg='#3d3d3d', relief=tk.RAISED, bd=2)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Status label
        self.status_label = tk.Label(
            status_frame,
            text="เข้าเชิฟเลย",
            font=("Arial", 12),
            fg='#ffffff',
            bg='#3d3d3d'
        )
        self.status_label.pack(pady=15)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            status_frame,
            mode='indeterminate',
            length=400
        )
        self.progress.pack(pady=(0, 15))
        self.progress.start(10)
    
    def toggle_debug(self):
        """เปิด/ปิดการแสดงข้อมูล debug"""
        if self.debug_var.get():
            self.debug_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
            self.debug_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.debug_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.root.geometry("500x500")
        else:
            self.debug_frame.pack_forget()
            self.root.geometry("500x300")
    
    def find_fivem_windows(self):
        """ค้นหาหน้าต่าง FiveM ทั้งหมด"""
        windows = []
        
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                
                # Check for FiveM window
                if BotConfig.FIVEM_WINDOW_TITLE in title:
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    
                    # Ensure window is large enough to be the game window
                    if width > 800 and height > 600:
                        windows.append({
                            'hwnd': hwnd,
                            'title': title,
                            'rect': rect,
                            'size': f"{width}x{height}"
                        })
            return True
        
        try:
            win32gui.EnumWindows(callback, None)
        except Exception as e:
            print(f"Error enumerating windows: {e}")
        
        return windows
    
    def detection_loop(self):
        """Loop การตรวจจับเกม"""
        detection_count = 0
        
        while self.is_detecting:
            try:
                detection_count += 1
                
                # Find FiveM windows
                fivem_windows = self.find_fivem_windows()
                
                if fivem_windows:
                    # Use the first valid window found
                    selected_window = fivem_windows[0]
                    hwnd = selected_window['hwnd']
                    
                    # Update UI in main thread
                    self.root.after(0, self.on_game_found, hwnd, selected_window)
                    break
                
                # Wait before next check
                time.sleep(2)
                
            except Exception as e:
                print(f"Detection error: {e}")
                time.sleep(3)
    
    def on_game_found(self, hwnd, window_info):
        """เมื่อพบเกมแล้ว"""
        # Stop progress bar
        self.progress.stop()
        
        # Update status
        self.status_label.config(
            text=f"✅ FiveM game detected!\n{window_info['title']} ({window_info['size']})",
            fg='#00ff88'
        )
        
        # Wait a moment then launch main bot
        self.root.after(2000, lambda: self.launch_main_bot(hwnd))
    
    def launch_main_bot(self, hwnd):
        """เปิดใช้งาน main bot"""
        try:
            # Stop detection
            self.is_detecting = False
            
            # Hide this window
            self.root.withdraw()
            
            # Call the callback to launch main bot
            self.on_game_detected(hwnd)
            
            # Close this window
            self.root.quit()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch main bot: {e}")
            self.on_close()
    
    def start_detection(self):
        """เริ่มการตรวจจับ"""
        self.is_detecting = True
        self.detection_thread = threading.Thread(target=self.detection_loop, daemon=True)
        self.detection_thread.start()
    
    def on_close(self):
        """ปิดโปรแกรม"""
        self.is_detecting = False
        self.root.quit()
        sys.exit(0)
    
    def run(self):
        """เริ่มต้น GUI"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"GUI Error: {e}")
        finally:
            self.is_detecting = False