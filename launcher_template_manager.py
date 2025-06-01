# -*- coding: utf-8 -*-
# template_manager.py - Template Management
import cv2
import os
from launcher_config import BotConfig, resource_path

class TemplateManager:
    def __init__(self):
        self.templates = {}
        
    def auto_load_templates(self):
        """โหลด template images อัตโนมัติ"""
        # ลบ template เก่าทิ้งก่อนโหลดใหม่
        self.templates.clear()
        
        # โหลด template ตามที่กำหนดใน config
        for template_file in BotConfig.TEMPLATE_FILES:
            # สร้าง path สัมพัทธ์และใช้ resource_path เพื่อรองรับ .py/.exe
            rel_path = os.path.join('assets', template_file)
            file_path = resource_path(rel_path)

            if os.path.exists(file_path):
                try:
                    # อ่านภาพเป็น grayscale
                    template = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
                    if template is not None:
                        key = template_file.split('.')[0].upper()
                        self.templates[key] = template
                except Exception:
                    # ข้ามหากอ่านไฟล์ไม่ได้
                    continue
        
        # ตรวจสอบว่ามี template ครบตามต้องการ
        required_keys = set(BotConfig.KEY_MAP.keys())
        return all(key in self.templates for key in required_keys)
    
    def get_templates(self):
        """ส่งคืน templates ทั้งหมด"""
        return self.templates.copy()