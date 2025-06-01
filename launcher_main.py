# -*- coding: utf-8 -*-
# main.py - Enhanced FiveM Fishing Bot Controller (Launcher Access Only)
# ═══════════════════════════════════════════════════════════════════════════════════════
# 🎣 FiveM Fishing Bot - Advanced Automation System
# Author: Your Name
# Version: 2.0
# Description: Intelligent fishing automation bot for FiveM with advanced detection
# ═══════════════════════════════════════════════════════════════════════════════════════

import threading
import time
import sys
import inspect
from typing import Optional, Dict, Any

# Core imports
from launcher_config import BotConfig
from launcher_window_manager import WindowManager
from launcher_template_manager import TemplateManager
from launcher_key_detector import KeyDetector
from launcher_key_executor import KeyExecutor
from launcher_gui_interface import GUIInterface


class FiveMFishingBot:
    """
    🎣 Advanced FiveM Fishing Bot Controller
    
    A sophisticated automation system for FiveM fishing minigames featuring:
    - Intelligent area detection
    - Optimized screenshot management
    - Secure launcher-only access
    - Advanced key sequence detection and execution
    """
    
    # Performance constants
    SCREENSHOT_INTERVAL = 0.5        # Screenshot frequency (5 fps)
    MAIN_LOOP_DELAY = 0.15          # Main loop delay (6.7 iterations/sec)
    POST_EXECUTION_DELAY = 1.5       # Delay after successful execution
    AREA_TEST_DURATION = 1.5         # Area testing duration
    FAILED_SCREENSHOT_DELAY = 0.8    # Delay after screenshot failure
    CRITICAL_FAILURE_DELAY = 1.0     # Delay after multiple failures
    
    def __init__(self, detected_hwnd: Optional[int] = None):
        """
        Initialize the FiveM Fishing Bot
        
        Args:
            detected_hwnd: Pre-detected window handle (optional)
            _launcher_token: Security token from launcher
        """
        
        # 🎯 Core components initialization
        self._initialize_components()
        
        # 🪟 Window setup
        self._setup_window(detected_hwnd)
        
        # 🤖 Bot state management
        self._initialize_bot_state()
        
        # 📊 Performance optimization
        self._initialize_performance_tracking()
        
        # 🚀 Initialize bot systems
        self.initialize_bot()
    
    def _initialize_components(self) -> None:
        """Initialize all core components"""
        self.window_manager = WindowManager()
        self.template_manager = TemplateManager()
        self.key_detector = None
        self.key_executor = KeyExecutor()
        self.gui = GUIInterface(self.toggle_bot)
    
    def _setup_window(self, detected_hwnd: Optional[int]) -> None:
        """Setup FiveM window if provided"""
        if detected_hwnd:
            self.window_manager.fivem_window = detected_hwnd
            if (BotConfig.DEBUG_MODE):
                self.gui.log_message(f"🎯 Using detected FiveM window (Handle: {detected_hwnd})")
    
    def _initialize_bot_state(self) -> None:
        """Initialize bot operational state"""
        self.is_running = False
        self.bot_thread = None
    
    def _initialize_performance_tracking(self) -> None:
        """Initialize performance optimization variables"""
        self.last_screenshot_time = 0
        self.last_screenshot = None
        self.screenshot_failed_count = 0
    
    def _validate_call_stack(self) -> bool:
        """Validate that the call originated from launcher.py"""
        frame = inspect.currentframe()
        try:
            caller_frames = inspect.getouterframes(frame)
            return any('launcher.py' in caller_frame.filename for caller_frame in caller_frames)
        finally:
            del frame
    
    def _deny_access(self) -> None:
        """Handle unauthorized access attempts"""
        print("❌ Access Denied: This bot can only be started through the official launcher!")
        print("🚀 Please run launcher.py to start the bot")
        sys.exit(1)
    
    def initialize_bot(self) -> None:
        """
        🚀 Initialize bot systems and validate configuration
        """
        
        # Find and validate FiveM window
        self._initialize_window()
        
        # Load and validate templates
        self._initialize_templates()
    
    def _initialize_window(self) -> None:
        """Initialize FiveM window detection"""
        if not self.window_manager.get_window_handle():
            if self.window_manager.find_fivem_window():
                if (BotConfig.DEBUG_MODE):
                    self.gui.log_message("🪟 FiveM window found successfully")
            else:
                if (BotConfig.DEBUG_MODE):
                    self.gui.log_message("⚠️ FiveM window not found!")
    
    def _initialize_templates(self) -> None:
        """Initialize template loading and key detection"""
        if self.template_manager.auto_load_templates():
            templates = self.template_manager.get_templates()
            self.key_detector = KeyDetector(templates)
            if (BotConfig.DEBUG_MODE):
                self.gui.log_message("📁 All templates loaded successfully!")
        else:
            templates = self.template_manager.get_templates()
            if templates:
                self.key_detector = KeyDetector(templates)
                if (BotConfig.DEBUG_MODE):
                    self.gui.log_message("📁 Partial templates loaded")
            else:
                if (BotConfig.DEBUG_MODE):
                    self.gui.log_message("⚠️ Warning: No template files found!")
    
    def get_current_screen(self) -> Optional[Any]:
        """
        📸 Optimized screen capture with intelligent caching
        
        Returns:
            Screenshot data or None if capture failed
        """
        current_time = time.time()
        
        # Check if we need a new screenshot
        if self._should_use_cached_screenshot(current_time):
            return self.last_screenshot
        
        # Capture new screenshot
        return self._capture_new_screenshot(current_time)
    
    def _should_use_cached_screenshot(self, current_time: float) -> bool:
        """Check if cached screenshot should be used"""
        time_since_last = current_time - self.last_screenshot_time
        return (time_since_last < self.SCREENSHOT_INTERVAL and 
                self.last_screenshot is not None)
    
    def _capture_new_screenshot(self, current_time: float) -> Optional[Any]:
        """Capture and process new screenshot"""
        screen = self.window_manager.capture_fivem_screen()
        
        if screen is not None:
            self._handle_successful_screenshot(screen, current_time)
            return screen
        else:
            self._handle_failed_screenshot()
            return self.last_screenshot
    
    def _handle_successful_screenshot(self, screen: Any, current_time: float) -> None:
        """Handle successful screenshot capture"""
        self.last_screenshot = screen
        self.last_screenshot_time = current_time
        self.screenshot_failed_count = 0
    
    def _handle_failed_screenshot(self) -> None:
        """Handle failed screenshot attempts"""
        self.screenshot_failed_count += 1
        
        if self.screenshot_failed_count >= 3:
            if (BotConfig.DEBUG_MODE):
                self.gui.log_message("⚠️ Multiple screenshot failures detected, increasing delay...")
            time.sleep(self.CRITICAL_FAILURE_DELAY)
            self.screenshot_failed_count = 0
        else:
            time.sleep(self.FAILED_SCREENSHOT_DELAY)
    
    def bot_loop(self) -> None:
        """
        🤖 Main bot execution loop with advanced logic
        
        Features:
        - Intelligent area detection and validation
        - Optimized performance with minimal resource usage
        - Robust error handling and recovery
        - Dynamic sequence detection and execution
        """
        # Initialize loop variables
        loop_state = self._initialize_loop_state()
        if (BotConfig.DEBUG_MODE):
            self.gui.log_message("🤖 Bot Started - Initializing intelligent detection...")
        
        while self.is_running:
            try:
                # Validate FiveM window connection
                if not self._validate_fivem_connection():
                    break
                
                # Get optimized screen capture
                screen = self.get_current_screen()
                if screen is None:
                    time.sleep(0.5)
                    continue
                
                current_time = time.time()
                
                # Execute main detection logic
                self._execute_detection_logic(screen, current_time, loop_state)
                
                # Optimized loop timing
                time.sleep(self.MAIN_LOOP_DELAY)
                
            except Exception as e:
                if (BotConfig.DEBUG_MODE):
                    self.gui.log_message(f"🚨 Bot error: {str(e)}")
                time.sleep(1)
    
    def _initialize_loop_state(self) -> Dict[str, Any]:
        """Initialize loop state variables"""
        return {
            'last_sequence_str': "",
            'sequence_stable_start': None,
            'consecutive_same_detections': 0,
            'area_confirmed_good': False,
            'area_test_start_time': None,
            'test_success_count': 0
        }
    
    def _validate_fivem_connection(self) -> bool:
        """Validate FiveM window connection"""
        if not self.window_manager.get_window_handle():
            if not self.window_manager.find_fivem_window():
                if (BotConfig.DEBUG_MODE):
                    self.gui.log_message("❌ FiveM window lost! Returning to launcher...")
                self.is_running = False
                self.gui.close()
                return False
            else:
                time.sleep(0.5)
        return True
    
    def _execute_detection_logic(self, screen: Any, current_time: float, state: Dict[str, Any]) -> None:
        """Execute main detection and execution logic"""
        if not state['area_confirmed_good']:
            self._handle_area_detection(screen, current_time, state)
        else:
            self._handle_sequence_detection(screen, current_time, state)
    
    def _handle_area_detection(self, screen: Any, current_time: float, state: Dict[str, Any]) -> None:
        """Handle minigame area detection and validation"""
        if not self.key_detector or not self.key_detector.get_detection_area():
            if self.key_detector and self.key_detector.auto_detect_minigame_area(screen):
                area = self.key_detector.get_detection_area()
                if (BotConfig.DEBUG_MODE):
                    self.gui.log_message(f"🎯 Found potential area: {area} - Initiating validation...")
                state['area_test_start_time'] = current_time
                state['test_success_count'] = 0
        else:
            self._test_detection_area(screen, current_time, state)
    
    def _test_detection_area(self, screen: Any, current_time: float, state: Dict[str, Any]) -> None:
        """Test and validate detection area"""
        if state['area_test_start_time'] is None:
            state['area_test_start_time'] = current_time
            state['test_success_count'] = 0
            if (BotConfig.DEBUG_MODE):
                self.gui.log_message("🧪 Testing detection area reliability...")
            return
        
        current_sequence = self.key_detector.detect_key_sequence(screen)
        current_sequence_str = ' '.join(current_sequence)
        
        if current_sequence_str and len(current_sequence) >= 5:
            state['test_success_count'] += 1
            if (BotConfig.DEBUG_MODE):
                self.gui.log_message(f"🧪 Test reading: {current_sequence_str} (Success: {state['test_success_count']})")
            
            if len(current_sequence) >= BotConfig.TARGET_SEQUENCE_LENGTH:
                if self._test_execution(current_sequence, current_sequence_str):
                    state['area_confirmed_good'] = True
                    state['area_test_start_time'] = None
                    if (BotConfig.DEBUG_MODE):
                        self.gui.log_message("✅ Area validation PASSED! (Execution successful)")
                    time.sleep(1.0)
                    return
        
        self._finalize_area_test(current_time, state)
    
    def _test_execution(self, sequence: list, sequence_str: str) -> bool:
        """Test execute sequence for area validation"""
        hwnd = self.window_manager.get_window_handle()
        if self.key_executor.execute_key_sequence(sequence, hwnd):
            if (BotConfig.DEBUG_MODE):
                self.gui.log_message(f"🎯 Validation execution successful: {sequence_str}")
            return True
        else:
            if (BotConfig.DEBUG_MODE):
                self.gui.log_message("❌ Validation execution failed")
            return False
    
    def _finalize_area_test(self, current_time: float, state: Dict[str, Any]) -> None:
        """Finalize area testing process"""
        test_duration = current_time - state['area_test_start_time']
        if test_duration >= self.AREA_TEST_DURATION:
            self.gui.log_message(f"📊 Area test completed: {state['test_success_count']} successful readings")
            
            if state['test_success_count'] >= 2:
                state['area_confirmed_good'] = True
                state['area_test_start_time'] = None
                if (BotConfig.DEBUG_MODE):
                    self.gui.log_message("✅ Area validation PASSED! Proceeding with automation.")
            else:
                if (BotConfig.DEBUG_MODE):
                    self.gui.log_message(f"❌ Area validation FAILED ({state['test_success_count']} successful readings)")
                self._reset_area_detection(state)
    
    def _reset_area_detection(self, state: Dict[str, Any]) -> None:
        """Reset area detection for retry"""
        if self.key_detector:
            self.key_detector.key_sequence_area = None
        state['area_test_start_time'] = None
        state['test_success_count'] = 0
        time.sleep(1.0)
    
    def _handle_sequence_detection(self, screen: Any, current_time: float, state: Dict[str, Any]) -> None:
        """Handle main sequence detection and execution"""
        current_sequence = self.key_detector.detect_key_sequence(screen)
        current_sequence_str = ' '.join(current_sequence)
        
        if not current_sequence_str:
            self._reset_sequence_state(state)
            return
        
        if current_sequence_str == state['last_sequence_str']:
            self._handle_stable_sequence(current_sequence, current_sequence_str, current_time, state)
        else:
            self._handle_new_sequence(current_sequence_str, state)
    
    def _handle_stable_sequence(self, sequence: list, sequence_str: str, current_time: float, state: Dict[str, Any]) -> None:
        """Handle stable sequence detection"""
        state['consecutive_same_detections'] += 1
        
        if (state['consecutive_same_detections'] >= BotConfig.MIN_CONSECUTIVE_DETECTIONS and
            len(sequence) >= BotConfig.TARGET_SEQUENCE_LENGTH):
            
            if state['sequence_stable_start'] is None:
                state['sequence_stable_start'] = current_time
                if (BotConfig.DEBUG_MODE):
                    self.gui.log_message(f"⏳ Sequence stabilizing: {sequence_str}")
            elif (current_time - state['sequence_stable_start']) >= BotConfig.SEQUENCE_STABLE_TIME:
                self._execute_stable_sequence(sequence, sequence_str, state)
    
    def _execute_stable_sequence(self, sequence: list, sequence_str: str, state: Dict[str, Any]) -> None:
        """Execute validated stable sequence"""
        hwnd = self.window_manager.get_window_handle()
        if (BotConfig.DEBUG_MODE):
            self.gui.log_message(f"🎯 Executing sequence: {sequence_str}")
        
        try:
            success = self.key_executor.execute_key_sequence(sequence, hwnd)
            if success:
                if (BotConfig.DEBUG_MODE):
                    self.gui.log_message(f"✅ Execution complete: {len(sequence)} keys executed successfully")
                    self.gui.log_message("⏸️ Processing delay active...")
                time.sleep(self.POST_EXECUTION_DELAY)
            else:
                if (BotConfig.DEBUG_MODE):
                    self.gui.log_message("❌ Execution failed - Key executor returned False")
        except Exception as e:
            if (BotConfig.DEBUG_MODE):
                self.gui.log_message(f"❌ Execution error: {str(e)}")
        
        self._reset_sequence_state(state)
    
    def _handle_new_sequence(self, sequence_str: str, state: Dict[str, Any]) -> None:
        """Handle new sequence detection"""
        state['last_sequence_str'] = sequence_str
        state['sequence_stable_start'] = None
        state['consecutive_same_detections'] = 0
    
    def _reset_sequence_state(self, state: Dict[str, Any]) -> None:
        """Reset sequence detection state"""
        state['last_sequence_str'] = ""
        state['sequence_stable_start'] = None
        state['consecutive_same_detections'] = 0
    
    def toggle_bot(self) -> None:
        """
        🔄 Toggle bot automation state with comprehensive validation
        """
        if not self.is_running:
            self._start_bot()
        else:
            self._stop_bot()
    
    def _start_bot(self) -> None:
        """Start bot with full validation"""
        # Validate FiveM window
        if not self._validate_window_for_start():
            return
        
        # Validate templates
        if not self._validate_templates_for_start():
            return
        
        # Reset performance tracking
        self._reset_performance_tracking()
        
        # Start bot thread
        self.is_running = True
        self.gui.update_status(True)
        self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.bot_thread.start()
        if (BotConfig.DEBUG_MODE):
            self.gui.log_message("🚀 Bot automation started successfully!")
    
    def _validate_window_for_start(self) -> bool:
        """Validate FiveM window before starting"""
        if not self.window_manager.get_window_handle():
            if not self.window_manager.find_fivem_window():
                self.gui.show_warning("Warning", "ไม่พบหน้าต่าง FiveM!")
                return False
        return True
    
    def _validate_templates_for_start(self) -> bool:
        """Validate templates before starting"""
        if not self.template_manager.get_templates():
            if not self.template_manager.auto_load_templates():
                self.gui.show_warning("Warning", "ไม่พบไฟล์ template (W.png, A.png, S.png, D.png)!")
                return False
            else:
                templates = self.template_manager.get_templates()
                self.key_detector = KeyDetector(templates)
        return True
    
    def _reset_performance_tracking(self) -> None:
        """Reset performance tracking variables"""
        self.last_screenshot_time = 0
        self.last_screenshot = None
        self.screenshot_failed_count = 0
    
    def _stop_bot(self) -> None:
        """Stop bot automation"""
        self.is_running = False
        self.gui.update_status(False)
        if (BotConfig.DEBUG_MODE):
            self.gui.log_message("🛑 Bot automation stopped")
    
    def run(self) -> None:
        """
        🚀 Main application entry point with comprehensive error handling
        """
        try:
            self.gui.run()
        except Exception as e:
            if (BotConfig.DEBUG_MODE):
                self.gui.log_message(f"🚨 Unexpected error: {str(e)}")
                print(f"Critical error: {str(e)}")
        finally:
            self.is_running = False


# ═══════════════════════════════════════════════════════════════════════════════════════
# End of Enhanced FiveM Fishing Bot Controller
# ═══════════════════════════════════════════════════════════════════════════════════════