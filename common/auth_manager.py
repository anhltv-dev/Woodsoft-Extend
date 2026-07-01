import requests
import json
import os
from datetime import datetime
import keyring

# Service name for Windows Credential Manager
SERVICE_NAME = "WoodsoftDataAnalyzer2026"

class AuthManager:
    """Manages Woodsoft API authentication and license validation."""
    
    API_URL = "https://woodsoft.vn/optimizers/api/auth/login"
    
    def __init__(self):
        self.user_data = None
        self.access_token = None
        self.expiry_date = None
        self.is_authenticated = False

    def login(self, email, password):
        """
        Performs login request as specified in the cURL.
        Returns (success, message/data)
        """
        payload = {
            'email': email,
            'password': password
        }
        
        try:
            # Using multipart/form-data as indicated by --form in cURL
            response = requests.post(self.API_URL, data=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.user_data = data.get("user", {})
                    self.access_token = data.get("access_token")
                    self.is_authenticated = True
                    return True, data
                else:
                    return False, "Invalid response format"
            elif response.status_code == 401:
                return False, "Invalid email or password"
            else:
                return False, f"Server error: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def get_license_info(self, user_data=None):
        """
        Extracts ONLY dataAnlzExpDate from nesting_config.
        Access is granted IF AND ONLY IF this date is valid.
        Returns (is_valid, expiry_date_str, message)
        """
        if user_data is None:
            user_data = self.user_data
            
        if not user_data:
            return False, None, "No user data found"
            
        nesting_config_str = user_data.get("nesting_config", "")
        if not nesting_config_str:
            return False, None, "Service not activated"
            
        try:
            if isinstance(nesting_config_str, str):
                config = json.loads(nesting_config_str)
            else:
                config = nesting_config_str
                
            expiry_date_str = config.get("dataAnlzExpDate")
            if not expiry_date_str:
                return False, None, "Service not activated"
                
            d_obj = self._parse_any_date(expiry_date_str)
            if not d_obj:
                return False, None, "Invalid date format"

            # Today is 2026-03-12
            today = datetime(2026, 3, 12)
            
            # Normalize display to DD-MM-YYYY
            display_date = d_obj.strftime("%d-%m-%Y")
            
            if d_obj >= today:
                return True, display_date, "Valid"
            else:
                return False, display_date, "License expired"
                
        except json.JSONDecodeError:
            return False, None, "Error parsing configuration"
        except Exception as e:
            return False, None, f"Error: {str(e)}"

    def _parse_any_date(self, date_str):
        """Attempts to parse date in multiple common formats."""
        for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def _get_settings_path(self):
        """Returns the path to the auth settings file."""
        return os.path.join(os.path.abspath("."), "auth_settings.json")

    def save_auth_settings(self, email, password, remember):
        """
        Saves authentication settings. 
        Email is saved to JSON, but Password is saved to Windows Credential Manager.
        """
        settings = {
            "email": email,
            "remember": remember
        }
        
        try:
            # Save non-sensitive settings to JSON
            with open(self._get_settings_path(), "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
            
            # Save or Remove password from Windows Credential Manager
            if remember and password:
                keyring.set_password(SERVICE_NAME, email, password)
            else:
                try:
                    keyring.delete_password(SERVICE_NAME, email)
                except keyring.errors.PasswordDeleteError:
                    pass 
                    
        except Exception as e:
            print(f"Error saving auth settings: {e}")

    def load_auth_settings(self):
        """
        Loads authentication settings.
        Email from JSON, Password from Windows Credential Manager.
        """
        try:
            path = self._get_settings_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    
                email = settings.get("email", "")
                remember = settings.get("remember", False)
                password = ""
                
                if remember and email:
                    # Retrieve sensitive data from OS secure storage
                    password = keyring.get_password(SERVICE_NAME, email) or ""
                
                return {
                    "email": email,
                    "password": password,
                    "remember": remember
                }
        except Exception as e:
            print(f"Error loading auth settings: {e}")
            
        return {"email": "", "password": "", "remember": False}

    def validate_date(self, date_str):
        """
        Validates if the date_str (DD-MM-YYYY) is after today.
        """
        try:
            # Expected format: DD-MM-YYYY as seen in Success JSON: "31-03-2026"
            expiry_date = datetime.strptime(date_str, "%d-%m-%Y")
            # Set to local time provided in system prompt: 2026-03-12
            today = datetime(2026, 3, 12) 
            
            if expiry_date >= today:
                return True, "Valid"
            else:
                return False, "License expired"
        except ValueError:
            return False, "Invalid date format"
