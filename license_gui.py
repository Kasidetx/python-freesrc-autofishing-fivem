# -*- coding: utf-8 -*-
"""
แอปพลิเคชัน GUI สำหรับการเปิดใช้งานไลเซนส์ (อัปเดต)
ให้ส่วนติดต่อผู้ใช้ที่เป็นมิตรสำหรับการเปิดใช้งานไลเซนส์เท่านั้น
GUI นี้จะแสดงเมื่อยังไม่มีไลเซนส์ที่ถูกต้องอยู่
"""

import tkinter as tk
from tkinter import messagebox
import threading
import sys

from hardware_id import HardwareIDGenerator
from license_api import LicenseAPIClient
from config import APP_CONFIG

class LicenseActivationGUI:
    """
    แอปพลิเคชัน GUI สำหรับการเปิดใช้งานไลเซนส์เท่านั้น
    จะแสดงเฉพาะเมื่อยังไม่มีไลเซนส์ที่ถูกต้องอยู่
    """

    def __init__(self):
        """เริ่มต้นแอปพลิเคชัน GUI"""
        try:
            self.root = tk.Tk()
            self._setup_window()

            # รับ hardware ID
            self.hardware_id = HardwareIDGenerator.get_hardware_id()
            # สร้าง client สำหรับติดต่อ API
            self.api_client = LicenseAPIClient()

            # สถานะการประมวลผล
            self.is_processing = False

            # สร้าง UI (ไม่ต้องตรวจสอบไลเซนส์ที่มีอยู่)
            self.setup_ui()

        except Exception as e:
            messagebox.showerror(
                "ข้อผิดพลาดในการเริ่มต้น", f"ไม่สามารถเริ่มโปรแกรมได้: {str(e)}"
            )
            raise

    def _setup_window(self):
        """กำหนดคุณสมบัติของหน้าต่างหลัก"""
        self.root.title(APP_CONFIG.window_title)
        self.root.geometry(APP_CONFIG.window_size)
        icon_path = APP_CONFIG.get_icon_path()
        self.root.iconbitmap(icon_path)
        self.root.resizable(False, False)
        self.root.configure(bg=APP_CONFIG.theme["bg_color"])

        # จัดกึ่งกลางหน้าต่าง
        self.root.eval("tk::PlaceWindow . center")

        # จัดการเหตุการณ์ปิดหน้าต่าง
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def setup_ui(self):
        """สร้างส่วนติดต่อผู้ใช้"""
        try:
            # คอนเทนเนอร์หลัก
            main_frame = tk.Frame(
                self.root, bg=APP_CONFIG.theme["bg_color"], padx=30, pady=20
            )
            main_frame.place(relx=0.5, rely=0.5, anchor="center")

            self._create_license_input_section(main_frame)
            self._create_buttons(main_frame)

            # ตั้งค่าการโฟกัสเริ่มต้น
            self.key_entry.focus()

        except Exception as e:
            raise

    def _create_license_input_section(self, parent):
        """สร้างส่วนสำหรับกรอกคีย์ไลเซนส์"""
        license_frame = tk.Frame(parent, bg=APP_CONFIG.theme["bg_color"])
        license_frame.grid(row=2, column=0, columnspan=2, pady=(10, 20), sticky="ew")

        # ป้ายแสดงสถานะ / คำแนะนำ
        self.status_label = tk.Label(
            license_frame,
            text="ใส่คีย์ของคุณ",
            font=("Arial", 10, "bold"),
            bg=APP_CONFIG.theme["bg_color"],
            fg=APP_CONFIG.theme["text_color"],
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        # ช่องกรอกคีย์
        self.key_entry = tk.Entry(
            license_frame,
            width=50,
            font=("Courier", 11),
            relief="solid",
            bd=1,
            validate="key",
            validatecommand=(self.root.register(self._validate_key_input), "%P"),
        )
        self.key_entry.grid(row=1, column=0, pady=(5, 0), sticky="ew")
        license_frame.columnconfigure(0, weight=1)

        # ผูกอีเวนต์
        self.key_entry.bind("<Return>", lambda e: self._on_activate_clicked())
        self.key_entry.bind("<KeyRelease>", self._on_key_changed)

    def _create_buttons(self, parent):
        """สร้างส่วนปุ่มกด"""
        button_frame = tk.Frame(parent, bg=APP_CONFIG.theme["bg_color"])
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        # ปุ่มเปิดใช้งาน (Login)
        self.activate_button = tk.Button(
            button_frame,
            text="Login",
            command=self._on_activate_clicked,
            bg=APP_CONFIG.theme["primary_color"],
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=8,
            relief="flat",
            cursor="hand2",
            state="disabled",  # ปิดไว้ก่อนจนกว่าจะกรอกคีย์ครบ
        )
        self.activate_button.pack(side=tk.LEFT, padx=5)

    def _validate_key_input(self, value: str) -> bool:
        """ตรวจสอบค่า input ว่าเป็นเลขฐานสิบหกและไม่เกินความยาว"""
        # อนุญาตให้ว่างได้ และต้องเป็นตัวอักขระ hex เท่านั้น
        if not value:
            return True

        # จำกัดความยาวไม่เกิน 32 ตัวอักษร
        if len(value) > 32:
            return False

        # ตรวจสอบว่าเป็น hex จริง
        try:
            int(value, 16)
            return True
        except ValueError:
            return False

    def _on_key_changed(self, event):
        """จัดการเมื่อมีการเปลี่ยนแปลงในช่องกรอกคีย์"""
        key = self.key_entry.get().strip()

        # เปิด/ปิดปุ่มตามความถูกต้องของคีย์
        if len(key) == 32 and self._is_valid_hex(key):
            self.activate_button.config(state="normal")
        else:
            self.activate_button.config(state="disabled")

    def _is_valid_hex(self, value: str) -> bool:
        """ตรวจสอบว่าเป็นสตริงเลขฐานสิบหกหรือไม่"""
        try:
            int(value, 16)
            return True
        except ValueError:
            return False

    def _on_activate_clicked(self):
        """จัดการเมื่อคลิกปุ่มเปิดใช้งาน"""
        if self.is_processing:
            return

        key = self.key_entry.get().strip()

        if not key:
            messagebox.showerror("ข้อผิดพลาด", "กรุณาใส่คีย์ไลเซนส์")
            return

        if len(key) != 32:
            messagebox.showerror("ข้อผิดพลาด", "คีย์ต้องมีความยาว 32 ตัวอักษร")
            return

        if not self._is_valid_hex(key):
            messagebox.showerror(
                "ข้อผิดพลาด",
                "คีย์ต้องประกอบด้วยตัวอักษรเลขฐานสิบหกเท่านั้น (0-9, a-f)",
            )
            return

        self._activate_license(key)

    def _activate_license(self, key: str):
        """ส่งคำขอเปิดใช้งานไลเซนส์"""
        self._show_loading(True, "กำลังเปิดใช้งานไลเซนส์...")

        # ใช้เธรดเพื่อไม่ให้ UI ค้าง
        threading.Thread(
            target=self._activate_license_thread, args=(key,), daemon=True
        ).start()

    def _activate_license_thread(self, key: str):
        """เธรดสำหรับเปิดใช้งานไลเซนส์"""
        try:
            response = self.api_client.activate_license(self.hardware_id, key)

            # อัปเดต UI ในเธรดหลัก
            self.root.after(
                0, self._activation_complete, response.success, response.message
            )

        except Exception as e:
            self.root.after(
                0, self._activation_complete, False, f"เปิดใช้งานล้มเหลว: {str(e)}"
            )

    def _activation_complete(self, success: bool, message: str):
        """จัดการเมื่อเปิดใช้งานเสร็จสิ้น"""
        self._show_loading(False)

        if success:
            self.key_entry.delete(0, tk.END)
            messagebox.showinfo(
                "สำเร็จ",
                "เปิดใช้งานไลเซนส์เรียบร้อย!",
            )

            # ปิดหน้าต่างนี้ แล้วกลับไปหน้า Main
            self.root.destroy()
            
            # เปิดหน้า Main
            from main import LicenseManager
            license_manager = LicenseManager()
            license_manager.check_and_route()
        else:
            messagebox.showerror("เปิดใช้งานล้มเหลว", message)
            self._update_status(
                f"เปิดใช้งานล้มเหลว: {message}", APP_CONFIG.theme["error_color"]
            )

    def _show_loading(self, show: bool, message: str = "กำลังประมวลผล..."):
        """แสดง/ซ่อนสถานะกำลังประมวลผล"""
        self.is_processing = show

        if show:
            self.activate_button.config(state="disabled")
            self.key_entry.config(state="disabled")
            self._update_status(message, APP_CONFIG.theme["primary_color"])
        else:
            self.key_entry.config(state="normal")

            # เปิดใช้งานปุ่มถ้าคีย์ยังถูกต้อง
            key = self.key_entry.get().strip()
            if len(key) == 32 and self._is_valid_hex(key):
                self.activate_button.config(state="normal")

    def _update_status(self, message: str, color: str):
        """อัปเดตข้อความสถานะ"""
        self.status_label.config(text=message, fg=color)

    def _on_closing(self):
        """จัดการเมื่อปิดหน้าต่าง"""
        try:
            if hasattr(self, "api_client"):
                self.api_client.close()
        except Exception:
            pass
        finally:
            self.root.destroy()
            sys.exit(0)

    def run(self):
        """รันแอปพลิเคชัน GUI"""
        try:
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาดขณะทำงาน", f"เกิดข้อผิดพลาด: {str(e)}")
        finally:
            # ทำความสะอาด
            try:
                if hasattr(self, "api_client"):
                    self.api_client.close()
            except:
                pass