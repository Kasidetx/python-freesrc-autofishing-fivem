# -*- coding: utf-8 -*-
import sys
import time
import shutil
import requests
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import subprocess
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from config import APP_CONFIG

# ——— การตั้งค่า ———
@dataclass
class Config:
    GITHUB_OWNER: str = "Kasidetx"
    GITHUB_REPO: str = "jexter"
    CURRENT_VERSION: str = "2.0.1"
    INSTALL_DIR: Path = Path(__file__).parent.absolute()
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    CHUNK_SIZE: int = 8192
    UPDATE_DELAY: int = 2     # หน่วงเวลาก่อนอัปเดต (วินาที)

config = Config()

# ——— คลาสจัดการเวอร์ชัน ———
class VersionManager:
    """จัดการการเปรียบเทียบและตรวจสอบเวอร์ชัน"""
    
    @staticmethod
    def parse_version(version: str) -> Tuple[int, ...]:
        """แปลงสตริงเวอร์ชันเป็นทูเพิลสำหรับเปรียบเทียบ"""
        try:
            return tuple(map(int, version.strip("v").split(".")))
        except ValueError as e:
            raise ValueError(f"รูปแบบเวอร์ชันไม่ถูกต้อง: {version}") from e
    
    @staticmethod
    def is_newer(current: str, latest: str) -> bool:
        """ตรวจสอบว่าเวอร์ชันล่าสุดใหม่กว่าปัจจุบันหรือไม่"""
        try:
            return VersionManager.parse_version(latest) > VersionManager.parse_version(current)
        except ValueError:
            return False

# ——— คลาสจัดการไฟล์ ———
class FileManager:
    """จัดการการทำงานกับไฟล์สำหรับการอัปเดต"""
    
    @staticmethod
    def get_current_executable() -> Optional[Path]:
        """ค้นหาไฟล์ executable ปัจจุบัน"""
        if getattr(sys, 'frozen', False):
            return Path(sys.executable)
        for file_path in config.INSTALL_DIR.glob("*.exe"):
            if not any(suffix in file_path.name for suffix in ['.new', '.backup', 'update_restart']):
                return file_path
        return None
    
    @staticmethod
    def create_backup(file_path: Path) -> Path:
        """สร้างสำเนาสำรองของ executable ปัจจุบัน"""
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        if backup_path.exists():
            backup_path.unlink()
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    @staticmethod
    def verify_file_integrity(file_path: Path, expected_size: Optional[int] = None) -> bool:
        """ตรวจสอบความสมบูรณ์ของไฟล์ที่ดาวน์โหลด"""
        if not file_path.exists():
            return False
        file_size = file_path.stat().st_size
        if file_size == 0:
            return False
        if expected_size and file_size != expected_size:
            return False
        return True

# ——— คลาสเชื่อมต่อ GitHub API ———
class GitHubAPI:
    """จัดการการโต้ตอบกับ GitHub API"""
    
    def __init__(self):
        self.api_url = f"https://api.github.com/repos/{config.GITHUB_OWNER}/{config.GITHUB_REPO}/releases/latest"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'{config.GITHUB_REPO}-updater/{config.CURRENT_VERSION}'
        })
    
    def get_latest_release(self) -> Dict[str, Any]:
        """ดึงข้อมูล release ล่าสุดจาก GitHub"""
        for attempt in range(config.MAX_RETRIES):
            try:
                response = self.session.get(self.api_url, timeout=config.REQUEST_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                if not data.get('tag_name'):
                    raise ValueError("ข้อมูล release ไม่ถูกต้อง: ไม่มี tag_name")
                assets = data.get('assets', [])
                if not assets:
                    raise ValueError("ไม่พบไฟล์ assets ใน release ล่าสุด")
                exe_asset = next((asset for asset in assets if asset['name'].endswith('.exe')), None)
                if not exe_asset:
                    raise ValueError("ไม่พบไฟล์ .exe ใน assets")
                return {
                    'version': data['tag_name'],
                    'asset_name': exe_asset['name'],
                    'download_url': exe_asset['browser_download_url'],
                    'size': exe_asset.get('size', 0),
                    'published_at': data.get('published_at', ''),
                    'body': data.get('body', '')
                }
            except requests.RequestException:
                if attempt == config.MAX_RETRIES - 1:
                    raise
                time.sleep(2 ** attempt)
            except (ValueError, KeyError):
                raise
    
    def download_file(self, url: str, file_path: Path, progress_callback=None) -> bool:
        """ดาวน์โหลดไฟล์พร้อมแสดงความคืบหน้า"""
        try:
            with self.session.get(url, stream=True, timeout=config.REQUEST_TIMEOUT) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=config.CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback:
                                progress = (downloaded / total_size * 100) if total_size > 0 else 0
                                progress_callback(progress, downloaded, total_size)
            return True
        except Exception:
            if file_path.exists():
                file_path.unlink()
            return False

# ——— คลาส GUI สำหรับอัปเดตอัตโนมัติ ———
class AutoUpdaterGUI:
    """GUI สำหรับอัปเดตโปรแกรมอัตโนมัติ"""
    
    def __init__(self, root):
        self.root = root
        self.github_api = GitHubAPI()
        self.file_manager = FileManager()
        self.version_manager = VersionManager()
        self.current_executable = None
        self.update_data = None
        self.is_updating = False
        self.setup_window()
        self.create_widgets()
        self.start_update_check()
    
    def setup_window(self):
        """ตั้งค่าหน้าต่างหลัก"""
        self.root.title("Jexter.exe")
        self.root.geometry("600x250")
        icon_path = APP_CONFIG.get_icon_path()
        self.root.iconbitmap(icon_path)
        self.root.resizable(False, False)
        self.colors = {
            'bg': '#1e1e1e',
            'surface': '#2d2d2d',
            'primary': '#0078d4',
            'success': '#107c10',
            'error': '#d13438',
            'warning': '#ff8c00',
            'text': '#ffffff',
            'text_secondary': '#b0b0b0'
        }
        self.root.configure(bg=self.colors['bg'])
        self.setup_styles()
        self.center_window()
    
    def setup_styles(self):
        """กำหนดสไตล์ ttk"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        styles = {
            'Status.TLabel': {
                'background': self.colors['bg'],
                'foreground': self.colors['primary'],
                'font': ('Segoe UI', 10, 'bold')
            },
            'Info.TLabel': {
                'background': self.colors['bg'],
                'foreground': self.colors['text'],
                'font': ('Segoe UI', 10)
            },
            'Modern.Horizontal.TProgressbar': {
                'background': self.colors['primary'],
                'troughcolor': self.colors['surface'],
                'borderwidth': 0,
                'lightcolor': self.colors['primary'],
                'darkcolor': self.colors['primary']
            }
        }
        for style_name, cfg in styles.items():
            self.style.configure(style_name, **cfg)
    
    def center_window(self):
        """จัดกึ่งกลางหน้าต่าง"""
        self.root.update_idletasks()
        width, height = 600, 250
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        """สร้าง widget ต่างๆ"""
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=30, pady=30)
        version_frame = tk.Frame(main_frame, bg=self.colors['surface'], relief='raised', bd=1)
        version_frame.pack(fill='x', pady=(0, 20))
        self.current_version_label = ttk.Label(version_frame, 
                                              text=f"เวอร์ชันปัจจุบัน: {config.CURRENT_VERSION}", 
                                              style='Info.TLabel')
        self.current_version_label.pack(pady=(0, 5))
        self.latest_version_label = ttk.Label(version_frame, 
                                             text="เวอร์ชันล่าสุด: กำลังตรวจสอบ...", 
                                             style='Info.TLabel')
        self.latest_version_label.pack()
        status_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        status_frame.pack(fill='x', pady=(0, 20))
        self.status_label = ttk.Label(status_frame, text="เริ่มต้น...", style='Status.TLabel', background=self.colors['bg'])
        self.status_label.pack()
        progress_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        progress_frame.pack(fill='x', pady=(0, 20))
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame,
                                            variable=self.progress_var,
                                            style='Modern.Horizontal.TProgressbar',
                                            length=540)
        self.progress_bar.pack(pady=(0, 10))
        self.progress_label = ttk.Label(progress_frame, text="", style='Info.TLabel')
        self.progress_label.pack()
    
    def update_status(self, message: str, color: str = None):
        """อัปเดตข้อความสถานะ"""
        # ปรับข้อความและสีของเลเบลโดยตรง ไม่แก้ไขสไตล์ global
        self.status_label.config(text=message)
        if color:
            self.status_label.config(foreground=color)
        else:
            self.status_label.config(foreground=self.colors['primary'])
    
    def update_progress(self, value: float, text: str = ""):
        """อัปเดตแถบความคืบหน้า"""
        self.progress_var.set(value)
        self.progress_label.config(text=text)
        self.root.update_idletasks()
    
    def start_update_check(self):
        """เริ่มตรวจสอบการอัปเดตในเธรดใหม่"""
        self.update_thread = threading.Thread(target=self.check_for_updates, daemon=True)
        self.update_thread.start()
    
    def check_for_updates(self):
        """ตรวจสอบว่ามีอัปเดตหรือไม่"""
        try:
            self.root.after(0, lambda: self.update_status("กำลังเชื่อมต่อเชิฟเวอร์"))
            self.root.after(0, lambda: self.update_progress(10, "กำลังดึงข้อมูลจากเชิฟเวอร์"))
            release_data = self.github_api.get_latest_release()
            latest_version = release_data['version']
            self.root.after(0, lambda: self.latest_version_label.config(
                text=f"เวอร์ชันล่าสุด: {latest_version}"))
            self.root.after(0, lambda: self.update_progress(30, "เปรียบเทียบเวอร์ชัน"))
            if self.version_manager.is_newer(config.CURRENT_VERSION, latest_version):
                self.update_data = release_data
                self.root.after(0, lambda: self.update_status(
                    f"🎉 พบเวอร์ชันใหม่: {latest_version}!", self.colors['success']))
                self.root.after(0, lambda: self.update_progress(50, "พร้อมอัปเดต"))
                self.root.after(1000, self.start_update)
            else:
                self.root.after(0, lambda: self.update_status(
                    "✅ คุณใช้งานเวอร์ชันล่าสุดแล้ว", self.colors['success']))
                self.root.after(0, lambda: self.update_progress(100, "เวอร์ชั่นล่าสุดแล้ว"))
                self.root.after(3000, self.launch_main_app)
        except Exception as e:
            self.root.after(0, lambda: self.update_status(
                f"❌ ตรวจสอบอัปเดตล้มเหลว: {e}", self.colors['error']))
            self.root.after(0, lambda: self.update_progress(0, "ตรวจสอบล้มเหลว"))
            self.root.after(5000, self.launch_main_app)
    
    def start_update(self):
        """เริ่มกระบวนการอัปเดต"""
        if self.is_updating:
            return
        self.is_updating = True
        threading.Thread(target=self.perform_update, daemon=True).start()
    
    def perform_update(self):
        """ทำการอัปเดตไฟล์จริง"""
        try:
            self.root.after(0, lambda: self.update_status("🔄 เตรียมอัปเดต...", self.colors['warning']))
            self.current_executable = self.file_manager.get_current_executable()
            if not self.current_executable:
                raise RuntimeError("ไม่พบไฟล์ executable ปัจจุบัน")
            temp_file = self.current_executable.with_suffix('.tmp')
            self.root.after(0, lambda: self.update_status("⬇️ กำลังดาวน์โหลด...", self.colors['primary']))
            def callback(p, d, t):
                
                mb = d/1024/1024
                total_mb = t/1024/1024 if t>0 else 0
                text = f"ดาวน์โหลด: {mb:.1f} MB"
                if total_mb>0:
                    text += f" / {total_mb:.1f} MB"
                self.root.after(0, lambda: self.update_progress(50 + (p*0.4), text))
            success = self.github_api.download_file(self.update_data['download_url'], temp_file, callback)
            if not success or not self.file_manager.verify_file_integrity(temp_file, self.update_data.get('size')):
                raise RuntimeError("ดาวน์โหลดหรือไฟล์ผิดพลาด")
            self.root.after(0, lambda: self.update_status("🔧 กำลังติดตั้ง...", self.colors['warning']))
            self.root.after(0, lambda: self.update_progress(95, "เตรียมรีสตาร์ท"))
            self.prepare_restart(temp_file)
        except Exception as e:
            self.root.after(0, lambda: self.update_status(
                f"❌ อัปเดตล้มเหลว: {e}", self.colors['error']))
            self.root.after(0, lambda: self.update_progress(0, "อัปเดตล้มเหลว"))
            self.is_updating = False
            self.root.after(3000, self.launch_main_app)
    
    def prepare_restart(self, new_file: Path):
        """เตรียมสคริปต์รีสตาร์ท"""
        batch = f'''@echo off
setlocal enabledelayedexpansion

echo Waiting for update...
set "CURRENT_EXE={self.current_executable.name}"
set "NEW_FILE={new_file.name}"

:wait_loop
tasklist /fi "imagename eq !CURRENT_EXE!" | find /i "!CURRENT_EXE!" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_loop
)

echo ติดตั้งเวอร์ชันใหม่...
copy /y "!NEW_FILE!" "!CURRENT_EXE!" >nul

if errorlevel 1 (
    echo Failed to update! 
    echo Please press any key to continue...
    pause >nul
    exit /b 1
)

echo ล้างไฟล์ชั่วคราว...
del "!NEW_FILE!" >nul 2>&1

del "%~f0"'''            
        script = self.current_executable.parent / "update_restart.bat"
        script.write_text(batch, encoding='utf-8')
        self.root.after(0, lambda: self.update_status(
            "🎉 ติดตั้งเสร็จ! กำลังรีสตาร์ท...", self.colors['success']))
        self.root.after(0, lambda: self.update_progress(100, "รีสตาร์ทแอป"))
        subprocess.Popen([str(script)], cwd=str(self.current_executable.parent), creationflags=subprocess.CREATE_NEW_CONSOLE)
        self.root.after(2000, lambda: sys.exit(0))
    
    def launch_main_app(self):
        """เปิดแอปหลัก"""
        try:
            self.update_status("🚀 กำลังเปิดแอปหลัก...", self.colors['primary'])
            self.update_progress(100, "โหลดแอปหลัก")
            from main import LicenseManager
            self.root.withdraw()
            license_manager = LicenseManager()
            license_manager.check_and_route()
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดแอปหลัก: {e}")
            sys.exit(1)

def main():
    try:
        root = tk.Tk()
        app = AutoUpdaterGUI(root)
        root.mainloop()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        messagebox.showerror("ข้อผิดพลาดร้ายแรง", f"เกิดข้อผิดพลาด: {e}")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()