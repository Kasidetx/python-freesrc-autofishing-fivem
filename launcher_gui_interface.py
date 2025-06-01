# -*- coding: utf-8 -*-
# gui_interface.py - Enhanced Modern GUI Interface
# ═══════════════════════════════════════════════════════════════════════════════════════
# 🎨 FiveM Fishing Bot - Modern GUI Interface
# Author: Your Name
# Version: 2.0
# Description: Beautiful and intuitive GUI interface with modern design
# ═══════════════════════════════════════════════════════════════════════════════════════

import tkinter as tk
from tkinter import messagebox
import sys
import keyboard
from typing import Callable
from config import APP_CONFIG
import secrets

class GUIInterface:
    """
    🎨 Modern GUI Interface for FiveM Fishing Bot
    
    Features:
    - Clean, modern design with beautiful colors
    - Responsive layout with proper spacing
    - Visual status indicators
    - Global hotkey support (F6)
    - Professional appearance
    """
    
    # Color scheme - Modern dark theme
    COLORS = {
        'bg_primary': '#1e1e1e',      # Dark background
        'bg_secondary': '#2d2d2d',    # Card background
        'accent': '#00d4aa',          # Teal accent
        'success': '#4caf50',         # Green
        'danger': '#f44336',          # Red
        'warning': '#ff9800',         # Orange
        'text_primary': '#ffffff',    # White text
        'text_secondary': '#b0b0b0',  # Gray text
    }
    
    # Typography
    FONTS = {
        'title': ('Segoe UI', 16, 'bold'),
        'heading': ('Segoe UI', 12, 'bold'),
        'body': ('Segoe UI', 10),
        'button': ('Segoe UI', 11, 'bold'),
    }
    
    def __init__(self, toggle_callback: Callable):
        """
        Initialize the modern GUI interface
        
        Args:
            toggle_callback: Function to call when toggling bot state
        """
        self.toggle_callback = toggle_callback
        self.root = None
        self.status_label = None
        self.start_button = None
        self.is_running = False
        
        self._create_main_window()
        self._setup_hotkeys()
        self._configure_window_behavior()
    
    def _create_main_window(self) -> None:
        """Create and configure the main window"""
        self.root = tk.Tk()
        self.root.title(secrets.token_bytes(16))
        self.root.geometry("450x300")
        self.root.resizable(False, False)
        self.root.configure(bg=self.COLORS['bg_primary'])
        icon_path = APP_CONFIG.get_icon_path()
        self.root.iconbitmap(icon_path)
        
        # Make window stay on top
        self.root.attributes('-topmost', True)
        
        # Center window on screen
        self._center_window()
        
        # Create all GUI components
        self._create_interface()
    
    def _center_window(self) -> None:
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _setup_hotkeys(self) -> None:
        """Setup global hotkeys"""
        try:
            keyboard.add_hotkey('f6', self.toggle_callback)
        except Exception:
            pass  # Hotkey setup failed, continue without it
    
    def _configure_window_behavior(self) -> None:
        """Configure window closing behavior"""
        self.root.protocol("WM_DELETE_WINDOW", self.exit_program)
    
    def _create_interface(self) -> None:
        """Create the complete GUI interface"""
        # Main container with padding
        main_frame = tk.Frame(
            self.root, 
            bg=self.COLORS['bg_primary'],
            padx=30,
            pady=25
        )
        main_frame.pack(fill='both', expand=True)
        
        # Title section
        self._create_title_section(main_frame)
        
        # Status section
        self._create_status_section(main_frame)
        
        # Control section
        self._create_control_section(main_frame)
        
        # Info section
        self._create_info_section(main_frame)
    
    def _create_title_section(self, parent: tk.Widget) -> None:
        """Create the title section"""
        title_frame = tk.Frame(parent, bg=self.COLORS['bg_primary'])
        title_frame.pack(fill='x', pady=(0, 25))
        
        # Main title
        title_label = tk.Label(
            title_frame,
            text="ตกปลา",
            font=self.FONTS['title'],
            fg=self.COLORS['text_primary'],
            bg=self.COLORS['bg_primary']
        )
        title_label.pack()
        
        # Subtitle
        subtitle_label = tk.Label(
            title_frame,
            text="Good Town",
            font=self.FONTS['body'],
            fg=self.COLORS['text_secondary'],
            bg=self.COLORS['bg_primary']
        )
        subtitle_label.pack(pady=(5, 0))
    
    def _create_status_section(self, parent: tk.Widget) -> None:
        """Create the status display section"""
        # Status card
        status_card = tk.Frame(
            parent,
            bg=self.COLORS['bg_secondary'],
            relief='flat',
            bd=0
        )
        status_card.pack(fill='x', pady=(0, 20))
        
        # Add some padding inside the card
        status_inner = tk.Frame(status_card, bg=self.COLORS['bg_secondary'])
        status_inner.pack(fill='x', padx=20, pady=15)
        
        # Status header
        status_header = tk.Label(
            status_inner,
            text="F6 - Start/Stop",
            font=self.FONTS['heading'],
            fg=self.COLORS['text_primary'],
            bg=self.COLORS['bg_secondary']
        )
        status_header.pack()
        
        # Status indicator
        self.status_label = tk.Label(
            status_inner,
            text="หยุดทำงาน",
            font=self.FONTS['button'],
            fg=self.COLORS['danger'],
            bg=self.COLORS['bg_secondary']
        )
        self.status_label.pack(pady=(8, 0))
    
    def _create_control_section(self, parent: tk.Widget) -> None:
        """Create the control buttons section"""
        control_frame = tk.Frame(parent, bg=self.COLORS['bg_primary'])
        control_frame.pack(fill='x', pady=(0, 20))
        
        # Main control button
        self.start_button = tk.Button(
            control_frame,
            text="เริ่มบอท",
            font=self.FONTS['button'],
            bg=self.COLORS['success'],
            fg=self.COLORS['text_primary'],
            activebackground=self._darken_color(self.COLORS['success']),
            activeforeground=self.COLORS['text_primary'],
            relief='flat',
            bd=0,
            padx=30,
            pady=12,
            cursor='hand2',
            command=self.toggle_callback
        )
        self.start_button.pack()
        
        # Add hover effects
        self._add_button_hover_effects(self.start_button)
    
    def _create_info_section(self, parent: tk.Widget) -> None:
        """Create the information section"""
        info_frame = tk.Frame(parent, bg=self.COLORS['bg_primary'])
        info_frame.pack(fill='x')
        
        # Hotkey info
        hotkey_label = tk.Label(
            info_frame,
            text="💡 กด F6 เพื่อเปิด/ปิด",
            font=self.FONTS['body'],
            fg=self.COLORS['text_secondary'],
            bg=self.COLORS['bg_primary']
        )
        hotkey_label.pack()
        
        # Version info
        version_label = tk.Label(
            info_frame,
            text="v2.0 - Enhanced Edition",
            font=('Segoe UI', 8),
            fg=self.COLORS['text_secondary'],
            bg=self.COLORS['bg_primary']
        )
        version_label.pack(pady=(10, 0))
    
    def _add_button_hover_effects(self, button: tk.Button) -> None:
        """Add hover effects to button"""
        original_bg = button.cget('bg')
        hover_bg = self._darken_color(original_bg)
        
        def on_enter(event):
            button.configure(bg=hover_bg)
        
        def on_leave(event):
            button.configure(bg=original_bg)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def _darken_color(self, color: str) -> str:
        """Darken a hex color for hover effects"""
        color_map = {
            self.COLORS['success']: '#45a049',
            self.COLORS['danger']: '#da190b',
            self.COLORS['accent']: '#00b894',
        }
        return color_map.get(color, color)
    
    def update_status(self, is_running: bool) -> None:
        """
        Update the bot status display
        
        Args:
            is_running: Current bot running state
        """
        self.is_running = is_running
        
        if is_running:
            # Running state
            self.status_label.config(
                text="● กำลังบอท",
                fg=self.COLORS['success']
            )
            self.start_button.config(
                text="🛑 หยุดบอท",
                bg=self.COLORS['danger']
            )
        else:
            # Stopped state
            self.status_label.config(
                text="● หยุดทำงาน",
                fg=self.COLORS['danger']
            )
            self.start_button.config(
                text="🚀 กำลังบอท",
                bg=self.COLORS['success']
            )
        
        # Update button hover effects
        self._add_button_hover_effects(self.start_button)
    
    def log_message(self, message: str) -> None:
        """
        Log message (silent - no GUI display)
        
        Args:
            message: Message to log
        """
        # Messages are logged silently - no GUI display
        # This maintains compatibility with the main bot code
        pass
    
    def show_warning(self, title: str, message: str) -> None:
        """
        Show warning dialog
        
        Args:
            title: Dialog title
            message: Warning message
        """
        messagebox.showwarning(title, message)
    
    def show_info(self, title: str, message: str) -> None:
        """
        Show information dialog
        
        Args:
            title: Dialog title
            message: Information message
        """
        messagebox.showinfo(title, message)
    
    def show_error(self, title: str, message: str) -> None:
        """
        Show error dialog
        
        Args:
            title: Dialog title
            message: Error message
        """
        messagebox.showerror(title, message)
    
    def run(self) -> None:
        """Start the GUI main loop"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.exit_program()
        except Exception as e:
            print(f"GUI Error: {str(e)}")
            self.exit_program()
    
    def close(self) -> None:
        """Close the GUI window"""
        if self.root:
            self.root.quit()
    
    def exit_program(self) -> None:
        """Exit the program gracefully"""
        try:
            # Clean up hotkeys
            keyboard.unhook_all()
        except Exception:
            pass
        
        if self.root:
            self.root.destroy()
        
        sys.exit(0)


# ═══════════════════════════════════════════════════════════════════════════════════════
# End of Enhanced GUI Interface
# ═══════════════════════════════════════════════════════════════════════