# -*- coding: utf-8 -*-
"""
License API client for handling license activation and verification
"""
import requests
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from config import API_CONFIG

@dataclass
class LicenseResponse:
    """Response from license API operations"""
    success: bool
    message: str
    data: Optional[Dict] = None

class LicenseAPIError(Exception):
    """Custom exception for license API errors"""
    pass

class LicenseAPIClient:
    """
    Client for handling license-related API operations
    Provides methods for license activation and verification
    """
    
    def __init__(self):
        """Initialize the API client with configuration"""
        self.base_url = API_CONFIG.base_url
        self.headers = API_CONFIG.headers
        self.timeout = API_CONFIG.timeout
        
        # Create session for connection reuse
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def verify_license(self, hardware_id: str) -> LicenseResponse:
        """
        Verify if a license exists for the given hardware ID
        
        Args:
            hardware_id: The hardware ID to verify
            
        Returns:
            LicenseResponse with verification result
        """
        try:
            
            # Validate input
            if not hardware_id or not isinstance(hardware_id, str):
                return LicenseResponse(
                    success=False,
                    message="Invalid hardware ID provided"
                )
            
            # Make API request
            response = self.session.post(
                f"{self.base_url}/verify",
                json={"hwid": hardware_id},
                timeout=self.timeout
            )
            
            # Handle response
            return self._handle_response(response, "License verification")
            
        except requests.exceptions.Timeout:
            return LicenseResponse(
                success=False,
                message="Request timed out. Please check your internet connection."
            )
        except requests.exceptions.ConnectionError:
            return LicenseResponse(
                success=False,
                message="Unable to connect to license server. Please check your internet connection."
            )
        except Exception as e:
            return LicenseResponse(
                success=False,
                message=f"Verification failed: {str(e)}"
            )
    
    def activate_license(self, hardware_id: str, license_key: str) -> LicenseResponse:
        """
        Activate a license with the given hardware ID and license key
        
        Args:
            hardware_id: The hardware ID for activation
            license_key: The license key to activate
            
        Returns:
            LicenseResponse with activation result
        """
        try:
            
            # Validate inputs
            validation_result = self._validate_activation_inputs(hardware_id, license_key)
            if not validation_result.success:
                return validation_result
            
            # Prepare payload
            payload = {
                "hwid": hardware_id,
                "key": license_key.lower().strip()
            }
            
            # Make API request
            response = self.session.post(
                f"{self.base_url}/activate",
                json=payload,
                timeout=self.timeout
            )
            
            # Handle response
            return self._handle_response(response, "License activation")
            
        except requests.exceptions.Timeout:
            return LicenseResponse(
                success=False,
                message="Activation timed out. Please try again."
            )
        except requests.exceptions.ConnectionError:
            return LicenseResponse(
                success=False,
                message="Unable to connect to license server. Please check your internet connection."
            )
        except Exception as e:
            return LicenseResponse(
                success=False,
                message=f"Activation failed: {str(e)}"
            )
    
    def _validate_activation_inputs(self, hardware_id: str, license_key: str) -> LicenseResponse:
        """Validate inputs for license activation"""
        
        # Validate hardware ID
        if not hardware_id or not isinstance(hardware_id, str):
            return LicenseResponse(
                success=False,
                message="Invalid hardware ID"
            )
        
        # Validate license key
        if not license_key or not isinstance(license_key, str):
            return LicenseResponse(
                success=False,
                message="License key is required"
            )
        
        # Clean and validate key format
        clean_key = license_key.strip().lower()
        
        if len(clean_key) != 32:
            return LicenseResponse(
                success=False,
                message="Invalid key format. Key must be 32 characters long."
            )
        
        # Validate hexadecimal format
        try:
            int(clean_key, 16)
        except ValueError:
            return LicenseResponse(
                success=False,
                message="Invalid key format. Key must contain only hexadecimal characters (0-9, a-f)."
            )
        
        return LicenseResponse(success=True, message="Validation passed")
    
    def _handle_response(self, response: requests.Response, operation: str) -> LicenseResponse:
        """
        Handle API response and return structured result
        
        Args:
            response: The requests response object
            operation: Description of the operation for logging
            
        Returns:
            LicenseResponse with parsed result
        """
        try:
            # Check if response is successful
            if not response.ok:
                
                # Try to get error message from response
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", f"Server error ({response.status_code})")
                except:
                    error_message = f"Server error ({response.status_code})"
                
                return LicenseResponse(
                    success=False,
                    message=error_message
                )
            
            # Parse JSON response
            try:
                data = response.json()
            except ValueError as e:
                return LicenseResponse(
                    success=False,
                    message="Invalid response from server"
                )
            
            # Extract result
            success = data.get("success", False)
            message = data.get("message", "Operation completed")
            
            return LicenseResponse(
                success=success,
                message=message,
                data=data
            )
            
        except Exception as e:
            return LicenseResponse(
                success=False,
                message=f"Failed to process server response: {str(e)}"
            )
    
    def close(self):
        """Close the session"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

# Convenience functions for backward compatibility
def verify_license(hardware_id: str) -> Tuple[bool, str]:
    """
    Convenience function for license verification
    Returns tuple of (success, message) for backward compatibility
    """
    with LicenseAPIClient() as client:
        response = client.verify_license(hardware_id)
        return response.success, response.message

def activate_license(hardware_id: str, license_key: str) -> Tuple[bool, str]:
    """
    Convenience function for license activation  
    Returns tuple of (success, message) for backward compatibility
    """
    with LicenseAPIClient() as client:
        response = client.activate_license(hardware_id, license_key)
        return response.success, response.message