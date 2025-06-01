# -*- coding: utf-8 -*-
"""
Hardware ID generation module
Generates unique hardware-based identifiers for license validation
"""
import hashlib
import platform
import subprocess
import uuid
import psutil
from typing import List, Optional
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False

class HardwareIDGenerator:
    """
    Generates hardware-based unique identifiers for license validation
    Uses multiple hardware components to create a stable, unique ID
    """
    
    @staticmethod
    def get_hardware_id() -> str:
        """
        Generate Hardware ID from real machine data - difficult to fake
        Returns a SHA256 hash of combined hardware information
        """
        try:
            hardware_components = HardwareIDGenerator._collect_hardware_info()
            
            if hardware_components:
                # Sort components to ensure consistent output
                combined_data = "|".join(sorted(hardware_components))
                hardware_id = hashlib.sha256(combined_data.encode("utf-8")).hexdigest()
                return hardware_id
            else:
                return HardwareIDGenerator._get_fallback_id()
                
        except Exception as e:
            return HardwareIDGenerator._get_fallback_id()
    
    @staticmethod
    def _collect_hardware_info() -> List[str]:
        """Collect all available hardware information"""
        hardware_components = []
        
        # Collection methods with error handling
        collectors = [
            HardwareIDGenerator._get_cpu_info,
            HardwareIDGenerator._get_motherboard_info,
            HardwareIDGenerator._get_bios_info,
            HardwareIDGenerator._get_storage_info,
            HardwareIDGenerator._get_mac_address,
            HardwareIDGenerator._get_system_uuid
        ]
        
        for collector in collectors:
            try:
                info = collector()
                if info:
                    hardware_components.append(info)
            except Exception as e:
                continue
        
        return hardware_components
    
    @staticmethod
    def _get_cpu_info() -> Optional[str]:
        """Get CPU information"""
        if platform.system() != "Windows":
            return None
            
        try:
            # Try WMI first if available
            if WMI_AVAILABLE:
                c = wmi.WMI()
                for cpu in c.Win32_Processor():
                    if cpu.ProcessorId and cpu.ProcessorId.strip():
                        return f"CPU:{cpu.ProcessorId.strip()}"
            
            # Fallback to wmic command
            result = subprocess.check_output(
                "wmic cpu get ProcessorId /value", 
                shell=True, 
                text=True,
                timeout=10  # Add timeout for security
            ).strip()
            
            for line in result.split("\n"):
                if "ProcessorId=" in line and "=" in line:
                    cpu_id = line.split("=")[1].strip()
                    if cpu_id:
                        return f"CPU:{cpu_id}"
                        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception) as e:
            raise
        return None
    
    @staticmethod
    def _get_motherboard_info() -> Optional[str]:
        """Get motherboard information"""
        if platform.system() != "Windows":
            return None
            
        try:
            if WMI_AVAILABLE:
                c = wmi.WMI()
                for board in c.Win32_BaseBoard():
                    if board.SerialNumber and board.SerialNumber.strip():
                        serial = board.SerialNumber.strip()
                        if HardwareIDGenerator._is_valid_serial(serial):
                            return f"MB:{serial}"
            
            # Fallback to wmic
            result = subprocess.check_output(
                "wmic baseboard get SerialNumber /value", 
                shell=True, 
                text=True,
                timeout=10
            ).strip()
            
            for line in result.split("\n"):
                if "SerialNumber=" in line:
                    serial = line.split("=")[1].strip()
                    if HardwareIDGenerator._is_valid_serial(serial):
                        return f"MB:{serial}"
                        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception) as e:
            raise
        return None
    
    @staticmethod
    def _get_bios_info() -> Optional[str]:
        """Get BIOS information"""
        if platform.system() != "Windows":
            return None
            
        try:
            if WMI_AVAILABLE:
                c = wmi.WMI()
                for bios in c.Win32_BIOS():
                    if bios.SerialNumber and bios.SerialNumber.strip():
                        return f"BIOS:{bios.SerialNumber.strip()}"
            
            # Fallback to wmic
            result = subprocess.check_output(
                "wmic bios get SerialNumber /value", 
                shell=True, 
                text=True,
                timeout=10
            ).strip()
            
            for line in result.split("\n"):
                if "SerialNumber=" in line:
                    serial = line.split("=")[1].strip()
                    if serial:
                        return f"BIOS:{serial}"
                        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception) as e:
            raise
        return None
    
    @staticmethod
    def _get_storage_info() -> Optional[str]:
        """Get primary storage device information"""
        if platform.system() != "Windows":
            return None
            
        try:
            if WMI_AVAILABLE:
                c = wmi.WMI()
                for disk in c.Win32_DiskDrive():
                    if disk.SerialNumber and disk.Size:  # Check for valid disk
                        serial = disk.SerialNumber.strip()
                        if len(serial) > 5:  # Valid serial length
                            return f"DISK:{serial}"
            
            # Fallback to wmic
            result = subprocess.check_output(
                "wmic diskdrive get SerialNumber /value",
                shell=True,
                text=True,
                timeout=10
            ).strip()
            
            for line in result.split("\n"):
                if "SerialNumber=" in line:
                    serial = line.split("=")[1].strip()
                    if serial and len(serial) > 5:
                        return f"DISK:{serial}"
                        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception) as e:
            raise
        return None
    
    @staticmethod
    def _get_mac_address() -> Optional[str]:
        """Get MAC address of primary network adapter"""
        try:
            # Use psutil to find active network interfaces
            for interface, addrs in psutil.net_if_addrs().items():
                # Skip loopback and virtual interfaces
                if any(skip in interface.lower() for skip in ["loopback", "virtual", "vmware", "vbox"]):
                    continue
                
                for addr in addrs:
                    if hasattr(psutil, 'AF_LINK') and addr.family == psutil.AF_LINK:
                        mac = addr.address
                        if mac and mac != "00:00:00:00:00:00" and len(mac) == 17:
                            return f"MAC:{mac}"
            
            # Fallback using uuid.getnode()
            mac_int = uuid.getnode()
            if mac_int != 0:  # Valid MAC found
                mac_hex = ":".join([
                    "{:02x}".format((mac_int >> elements) & 0xFF)
                    for elements in range(0, 2 * 6, 2)
                ][::-1])
                return f"MAC:{mac_hex}"
                
        except Exception as e:
            raise
        return None
    
    @staticmethod
    def _get_system_uuid() -> Optional[str]:
        """Get system UUID"""
        if platform.system() != "Windows":
            return None
            
        try:
            if WMI_AVAILABLE:
                c = wmi.WMI()
                for system in c.Win32_ComputerSystemProduct():
                    if system.UUID and system.UUID.strip():
                        uuid_val = system.UUID.strip()
                        if HardwareIDGenerator._is_valid_uuid(uuid_val):
                            return f"UUID:{uuid_val}"
            
            # Fallback to wmic
            result = subprocess.check_output(
                "wmic csproduct get UUID /value", 
                shell=True, 
                text=True,
                timeout=10
            ).strip()
            
            for line in result.split("\n"):
                if "UUID=" in line:
                    uuid_val = line.split("=")[1].strip()
                    if HardwareIDGenerator._is_valid_uuid(uuid_val):
                        return f"UUID:{uuid_val}"
                        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception) as e:
            raise
        return None
    
    @staticmethod
    def _is_valid_serial(serial: str) -> bool:
        """Check if serial number is valid (not placeholder)"""
        if not serial:
            return False
        
        invalid_serials = [
            "to be filled by o.e.m.",
            "default string",
            "not specified",
            "system serial number",
            "0123456789",
            "none"
        ]
        
        return serial.lower() not in invalid_serials and len(serial) > 3
    
    @staticmethod
    def _is_valid_uuid(uuid_str: str) -> bool:
        """Check if UUID is valid (not placeholder)"""
        if not uuid_str:
            return False
            
        # Check for common placeholder UUIDs
        invalid_uuids = [
            "03000200-0400-0500-0006-000700080009",
            "00000000-0000-0000-0000-000000000000",
            "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF"
        ]
        
        return uuid_str.upper() not in invalid_uuids
    
    @staticmethod
    def _get_fallback_id() -> str:
        """Generate fallback ID when hardware components are unavailable"""
        try:
            fallback_data = [
                f"NODE:{uuid.getnode()}",
                f"PLATFORM:{platform.machine()}",
                f"PROCESSOR:{platform.processor()}",
                f"SYSTEM:{platform.system()}",
                f"RELEASE:{platform.release()}",
            ]
            
            # Filter out empty values
            fallback_data = [item for item in fallback_data if item.split(":")[1]]
            
            combined = "|".join(fallback_data)
            return hashlib.sha256(combined.encode("utf-8")).hexdigest()
            
        except Exception as e:
            # Ultimate fallback
            return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()