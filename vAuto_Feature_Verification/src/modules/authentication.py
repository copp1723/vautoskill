"""
Authentication Module for vAuto Feature Verification System

This module handles authentication to the vAuto system, including:
- Login process
- Session management
- 2FA handling if required
- Authentication error detection and recovery
"""

import logging
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class AuthenticationModule:
    """
    Handles authentication to the vAuto system.
    """
    
    # Define selectors for the login page elements
    LOGIN_URL = "https://vauto.com/login"  # Replace with actual login URL
    USERNAME_FIELD = (By.ID, "username")  # Replace with actual selector
    PASSWORD_FIELD = (By.ID, "password")  # Replace with actual selector
    LOGIN_BUTTON = (By.ID, "loginButton")  # Replace with actual selector
    
    # Selectors for success/failure detection
    LOGIN_ERROR_MESSAGE = (By.CSS_SELECTOR, ".error-message")  # Replace with actual selector
    DASHBOARD_ELEMENT = (By.CSS_SELECTOR, ".dashboard-container")  # Replace with actual selector
    
    # 2FA related selectors (if applicable)
    TFA_INPUT_FIELD = (By.ID, "tfa-code")  # Replace with actual selector
    TFA_SUBMIT_BUTTON = (By.ID, "tfa-submit")  # Replace with actual selector
    
    def __init__(self, nova_engine, config):
        """
        Initialize the Authentication Module.
        
        Args:
            nova_engine: Initialized NovaActEngine instance
            config (dict): Configuration dictionary with auth settings
        """
        self.nova = nova_engine
        self.config = config
        self.logger = logging.getLogger('authentication')
        self.is_authenticated = False
    
    def login(self):
        """
        Perform the login process to vAuto.
        
        Returns:
            bool: True if login was successful, False otherwise
        """
        self.logger.info("Starting vAuto login process")
        
        # Navigate to login page
        if not self.nova.navigate_to(self.LOGIN_URL):
            self.logger.error("Failed to navigate to login page")
            return False
        
        # Input username
        if not self.nova.input_text(self.USERNAME_FIELD, self.config['username']):
            self.logger.error("Failed to input username")
            return False
        
        # Input password
        if not self.nova.input_text(self.PASSWORD_FIELD, self.config['password']):
            self.logger.error("Failed to input password")
            return False
        
        # Click login button
        if not self.nova.click_element(self.LOGIN_BUTTON):
            self.logger.error("Failed to click login button")
            return False
        
        # Check for 2FA if configured
        if self.config.get('requires_2fa', False):
            if not self.handle_2fa():
                self.logger.error("2FA handling failed")
                return False
        
        # Verify successful login
        if self.is_login_successful():
            self.is_authenticated = True
            self.logger.info("Login successful")
            return True
        else:
            self.logger.error("Login failed - could not verify successful login")
            return False
    
    def handle_2fa(self):
        """
        Handle two-factor authentication if required.
        
        Returns:
            bool: True if 2FA was successful, False otherwise
        """
        self.logger.info("Handling 2FA authentication")
        
        # Wait for 2FA input field to appear
        tfa_field = self.nova.wait_for_element(self.TFA_INPUT_FIELD)
        if not tfa_field:
            self.logger.error("2FA input field not found")
            return False
        
        # If we have a 2FA function configured, use it to get the code
        if callable(self.config.get('tfa_function')):
            try:
                tfa_code = self.config['tfa_function']()
                self.logger.info("Retrieved 2FA code")
            except Exception as e:
                self.logger.error(f"Failed to get 2FA code: {str(e)}")
                return False
        # Otherwise, use the static code from config (not recommended for production)
        elif 'tfa_static_code' in self.config:
            tfa_code = self.config['tfa_static_code']
            self.logger.warning("Using static 2FA code (not recommended for production)")
        else:
            self.logger.error("No 2FA code or function available")
            return False
        
        # Input the 2FA code
        if not self.nova.input_text(self.TFA_INPUT_FIELD, tfa_code):
            self.logger.error("Failed to input 2FA code")
            return False
        
        # Submit the 2FA code
        if not self.nova.click_element(self.TFA_SUBMIT_BUTTON):
            self.logger.error("Failed to submit 2FA code")
            return False
        
        # Wait for processing
        time.sleep(2)
        
        # Verify successful login after 2FA
        return self.is_login_successful()
    
    def is_login_successful(self):
        """
        Check if login was successful by looking for dashboard elements.
        
        Returns:
            bool: True if login was successful, False otherwise
        """
        # First, check if there's an error message
        if self.nova.is_element_present(self.LOGIN_ERROR_MESSAGE, timeout=2):
            error_text = self.nova.get_element_text(self.LOGIN_ERROR_MESSAGE)
            self.logger.error(f"Login error: {error_text}")
            return False
        
        # Check for dashboard element to confirm successful login
        return self.nova.is_element_present(self.DASHBOARD_ELEMENT, timeout=10)
    
    def logout(self):
        """
        Log out from vAuto.
        
        Returns:
            bool: True if logout was successful, False otherwise
        """
        if not self.is_authenticated:
            self.logger.info("Already logged out")
            return True
        
        # Implement logout logic here
        # For example:
        # - Click profile/menu button
        # - Click logout option
        # - Verify login page is displayed
        
        self.logger.info("Logout functionality not yet implemented")
        self.is_authenticated = False
        return True  # Placeholder
    
    def refresh_session(self):
        """
        Refresh the session if it's about to expire.
        
        Returns:
            bool: True if session refresh was successful, False otherwise
        """
        self.logger.info("Refreshing session")
        
        # Simple approach: just navigate to a known page within vAuto
        sample_page = self.config.get('session_refresh_url', self.LOGIN_URL)
        
        if not self.nova.navigate_to(sample_page):
            self.logger.error("Failed to refresh session")
            return False
        
        # Check if we're still logged in
        if not self.is_authenticated:
            self.logger.warning("Session expired, attempting to login again")
            return self.login()
        
        self.logger.info("Session refreshed successfully")
        return True
    
    def check_authentication(self):
        """
        Check if we're still authenticated.
        
        Returns:
            bool: True if still authenticated, False otherwise
        """
        # Look for an element that would only be visible when logged in
        return self.nova.is_element_present(self.DASHBOARD_ELEMENT, timeout=5)
    
    def ensure_authenticated(self):
        """
        Ensure we're authenticated, attempting login if necessary.
        
        Returns:
            bool: True if authenticated, False if authentication failed
        """
        if self.is_authenticated and self.check_authentication():
            return True
        
        self.logger.info("Not authenticated, attempting login")
        return self.login()
