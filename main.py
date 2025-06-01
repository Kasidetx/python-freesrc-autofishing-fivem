# -*- coding: utf-8 -*-
"""
Main entry point for license management system
Checks license status and routes user accordingly
"""

import tkinter as tk
from tkinter import messagebox
import sys

from hardware_id import HardwareIDGenerator
from license_api import LicenseAPIClient
from config import APP_CONFIG
# Removed LicenseActivationGUI import here (moved inside method)

class LicenseManager:
    """
    Main license manager that checks status and routes accordingly
    """
    
    def __init__(self):
        """Initialize the license manager"""
        try:
            self.hardware_id = HardwareIDGenerator.get_hardware_id()
            self.api_client = LicenseAPIClient()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize: {str(e)}")
            sys.exit(1)

    def check_and_route(self):
        """
        Check license status and route user to appropriate action
        """
        try:
            # Show loading window while checking
            splash = self._create_splash_window()
            splash.update()
            
            # Check if license exists for this hardware
            response = self.api_client.verify_license(self.hardware_id)
            
            # Close splash window
            splash.destroy()
            
            if response.success:
                # License exists and is valid - launch directly
                print("License found - launching application...")
                self._launch_application()
            else:
                # No license found - show activation GUI
                print("No license found - showing activation window...")
                self._show_activation_gui()
                
        except Exception as e:
            if 'splash' in locals():
                splash.destroy()
            messagebox.showerror("Error", f"License check failed: {str(e)}")
            sys.exit(1)
        finally:
            # Cleanup API client
            try:
                self.api_client.close()
            except:
                pass

    def _create_splash_window(self):
        """Create a simple splash screen while checking license"""
        splash = tk.Tk()
        splash.title("")
        splash.geometry("400x150")
        splash.resizable(False, False)
        splash.configure(bg=APP_CONFIG.theme.get("bg_color", "#f0f0f0"))
        
        # Center the window
        splash.eval("tk::PlaceWindow . center")
        
        # Remove window decorations for splash effect
        splash.overrideredirect(True)
        
        # Create content
        frame = tk.Frame(splash, bg=APP_CONFIG.theme.get("bg_color", "#f0f0f0"))
        frame.pack(expand=True, fill="both", padx=30, pady=30)
        
        # Title
        title_label = tk.Label(
            frame,
            text="Jekxer",
            font=("Arial", 14, "bold"),
            bg=APP_CONFIG.theme.get("bg_color", "#f0f0f0"),
            fg=APP_CONFIG.theme.get("text_color", "#000000")
        )
        title_label.pack(pady=(0, 20))
        
        # Status
        status_label = tk.Label(
            frame,
            text="กำลังตรวจสอบ...",
            font=("Arial", 10),
            bg=APP_CONFIG.theme.get("bg_color", "#f0f0f0"),
            fg=APP_CONFIG.theme.get("muted_color", "#666666")
        )
        status_label.pack()
        
        return splash

    def _launch_application(self):
        """Launch the main application (launcher.exe)"""
        try:
            # Import from launcher folder
            from launcher_launcher import FiveMFishingBotLauncher
            # Create instance and run
            launcher_instance = FiveMFishingBotLauncher()
            launcher_instance.run()
        except Exception as e:
            messagebox.showerror(
                "Launch Error",
                f"ไม่สามารถเริ่มแอปพลิเคชันได้:\n{e}\nกรุณาติดต่อทีมสนับสนุน"
            )
            sys.exit(1)

    def _show_activation_gui(self):
        """Show the license activation GUI"""
        try:
            # Import only when needed to avoid circular imports
            from license_gui import LicenseActivationGUI
            
            # Create and run activation GUI
            activation_gui = LicenseActivationGUI()
            activation_gui.run()
            
        except Exception as e:
            messagebox.showerror(
                "GUI Error", 
                f"Failed to show activation window:\n{str(e)}"
            )
            # Do not exit immediately, allow user to retry