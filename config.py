# -*- coding: utf-8 -*-
"""
Configuration settings for the license activation system
"""
from dataclasses import dataclass
from typing import Optional
import secrets
import sys
import os

def resource_path(relative_path):
    """ คืน path ที่ถูกต้องทั้งตอนรัน .py และ .exe """
    try:
        base_path = sys._MEIPASS  # ถูกใช้โดย PyInstaller ตอนรัน .exe
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

@dataclass
class APIConfig:
    """API configuration settings"""
    base_url: str
    authorization: str
    protection_bypass: Optional[str] = None
    timeout: int = 10

    @property
    def headers(self) -> dict:
        """Get API headers"""
        headers = {"Content-Type": "application/json"}
        if self.authorization:
            headers["Authorization"] = self.authorization
        if self.protection_bypass:
            headers["x-vercel-protection-bypass"] = self.protection_bypass
        return headers

@dataclass
class AppConfig:
    """Application configuration settings"""
    version: str
    window_title: str
    window_size: str
    theme: dict

    ICON_FILE = 'icon.ico'

    @classmethod
    def get_icon_path(cls):
        """
        คืน path เต็ม ๆ ของไฟล์ไอคอนใน assets/
        """
        return resource_path(os.path.join('assets', cls.ICON_FILE))

    @classmethod
    def default(cls):
        """Get default application configuration"""
        return cls(
            version="1.0.0",
            window_title=secrets.token_hex(32),
            window_size="550x250",
            theme={
                "bg_color": "#f0f0f0",
                "primary_color": "#3498db",
                "success_color": "#27ae60",
                "error_color": "#e74c3c",
                "text_color": "#2c3e50",
                "muted_color": "#7f8c8d"
            }
        )

# Load configuration from environment or use defaults
def load_config():
    """Load configuration from environment variables or use defaults"""
    api_config = APIConfig(
        base_url="https://backend-jekter.vercel.app/api",
        authorization="Bearer bananakingisjekxer",
        protection_bypass="rwSInwgJGPwjn53ealXJQ1mcT1Ce7xu3",
        timeout=10
    )
    app_config = AppConfig.default()
    return api_config, app_config

# Global configuration instances
API_CONFIG, APP_CONFIG = load_config()