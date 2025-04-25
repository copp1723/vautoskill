"""
Authentication Module for vAuto Feature Verification System.

Handles:
- Secure credential management
- vAuto login and session management
- Session validation and renewal
"""

import logging
import os
from datetime import datetime, timedelta
import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AuthenticationModule:
    """
    Module for handling vAuto authentication.
    """
    
    def __init__(self, nova_engine, config):
        """
        Initialize the authentication module.
        
        Args:
            nova_engine (NovaActEngine): Nova Act Engine instance
            config (dict): System configuration
        """
        self.nova_engine = nova_engine
        self.config = config
        self.session_valid_until = None
        
        # Get credentials from environment variables
        self.credentials = {
            "username": os.getenv("VAUTO_USERNAME"),
            "password": os.getenv("VAUTO_PASSWORD")
        }
        
        if not self.credentials["username"] or not self.credentials["password"]:
            logger.error("vAuto credentials not found in environment variables")
            raise ValueError("vAuto credentials are required (VAUTO_USERNAME and VAUTO_PASSWORD)")
        
        logger.info("Authentication module initialized")
    
    async def login(self, dealership_id=None):
        """
        Log in to vAuto.
        
        Args:
            dealership_id (str, optional): Dealership ID to select after login
            
        Returns:
            bool: True if login successful, False otherwise
        """
        logger.info("Logging in to vAuto")
        
        try:
            result = await self.nova_engine.execute_action(
                lambda browser: self._login_action(browser, dealership_id)
            )
            
            if result:
                # Set session expiration (default to 4 hours)
                self.session_valid_until = datetime.now() + timedelta(hours=4)
                logger.info("Successfully logged in to vAuto")
            else:
                logger.error("Failed to log in to vAuto")
            
            return result
            
        except Exception as e:
            logger.error(f"Error logging in to vAuto: {str(e)}")
            return False
    
    async def _login_action(self, browser, dealership_id):
        """
        Internal action to perform login.
        
        Args:
            browser: Browser instance
            dealership_id (str, optional): Dealership ID to select after login
            
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            # Navigate to login page
            await self.nova_engine.navigate_to("https://www.vauto.com/login")
            
            # Wait for the login form to load
            username_field = await self.nova_engine.wait_for_presence(By.ID, "username")
            if not username_field:
                logger.error("Login form not found")
                return False
            
            # Enter credentials
            await self.nova_engine.fill_input(By.ID, "username", self.credentials["username"])
            await self.nova_engine.fill_input(By.ID, "password", self.credentials["password"])
            
            # Click login button
            await self.nova_engine.click_element(By.XPATH, "//button[@type='submit' or contains(@class, 'login')]")
            
            # Wait for login to complete
            dashboard_selector = "//div[contains(@class, 'dashboard') or contains(@class, 'inventory')]"
            dashboard = await self.nova_engine.wait_for_presence(By.XPATH, dashboard_selector)
            
            if not dashboard:
                # Check for error messages
                error_message = await self._check_login_errors(browser)
                if error_message:
                    logger.error(f"Login failed: {error_message}")
                return False
            
            # Select dealership if specified
            if dealership_id:
                success = await self._select_dealership(dealership_id)
                return success
            
            return True
            
        except Exception as e:
            logger.error(f"Login action failed: {str(e)}")
            # Take a screenshot for debugging
            await self.nova_engine.take_screenshot("logs/login_failure.png")
            return False
    
    async def _check_login_errors(self, browser):
        """
        Check for login error messages.
        
        Args:
            browser: Browser instance
            
        Returns:
            str: Error message if found, None otherwise
        """
        error_selectors = [
            "//div[contains(@class, 'error')]",
            "//span[contains(@class, 'error')]",
            "//p[contains(@class, 'error')]",
            "//div[contains(@class, 'alert')]"
        ]
        
        for selector in error_selectors:
            try:
                elements = await self.nova_engine.find_elements(By.XPATH, selector)
                for element in elements:
                    text = await self.nova_engine.get_text(element)
                    if text and len(text.strip()) > 0 and "error" in text.lower():
                        return text.strip()
            except:
                continue
        
        return None
    
    async def _select_dealership(self, dealership_id):
        """
        Select a dealership after login.
        
        Args:
            dealership_id (str): Dealership ID to select
            
        Returns:
            bool: True if dealership selected successfully, False otherwise
        """
        logger.info(f"Selecting dealership: {dealership_id}")
        
        try:
            # Check if dealership dropdown is present
            dealer_dropdown = await self.nova_engine.find_element(
                By.XPATH, 
                "//div[contains(@class, 'dealerSelect') or contains(@class, 'dealer-select')]",
                timeout=5
            )
            
            if dealer_dropdown:
                # Click the dropdown to show options
                await self.nova_engine.click_element(dealer_dropdown)
                
                # Wait for dropdown options to appear
                await asyncio.sleep(1)
                
                # Look for the specified dealership
                dealership_option = await self.nova_engine.find_element(
                    By.XPATH,
                    f"//div[contains(text(), '{dealership_id}') or contains(@id, '{dealership_id}')]",
                    timeout=5
                )
                
                if dealership_option:
                    await self.nova_engine.click_element(dealership_option)
                    
                    # Wait for the page to refresh with selected dealership
                    await asyncio.sleep(2)
                    
                    logger.info(f"Successfully selected dealership: {dealership_id}")
                    return True
                else:
                    logger.error(f"Dealership not found: {dealership_id}")
                    return False
            
            # If no dropdown is found, we may already be in the correct dealership
            logger.info("No dealership selection needed")
            return True
            
        except Exception as e:
            logger.error(f"Error selecting dealership: {str(e)}")
            return False
    
    async def is_logged_in(self):
        """
        Check if the current session is logged in.
        
        Returns:
            bool: True if logged in, False otherwise
        """
        if not self.session_valid_until or datetime.now() > self.session_valid_until:
            return False
        
        try:
            result = await self.nova_engine.execute_action(self._check_logged_in_action)
            return result
        except Exception as e:
            logger.error(f"Error checking login status: {str(e)}")
            return False
    
    async def _check_logged_in_action(self, browser):
        """
        Internal action to check if logged in.
        
        Args:
            browser: Browser instance
            
        Returns:
            bool: True if logged in, False otherwise
        """
        try:
            # Check for login page
            login_elements = await self.nova_engine.find_elements(
                By.XPATH, 
                "//*[@id='username' or contains(@class, 'login')]",
                timeout=3
            )
            
            if login_elements:
                return False
            
            # Check for elements that indicate we're logged in
            dashboard_elements = await self.nova_engine.find_elements(
                By.XPATH,
                "//div[contains(@class, 'dashboard') or contains(@class, 'inventory') or contains(@class, 'navbar')]",
                timeout=3
            )
            
            return len(dashboard_elements) > 0
            
        except Exception as e:
            logger.warning(f"Check logged in action failed: {str(e)}")
            return False
    
    async def ensure_logged_in(self, dealership_id=None):
        """
        Ensure the session is logged in, logging in if necessary.
        
        Args:
            dealership_id (str, optional): Dealership ID to select if login is needed
            
        Returns:
            bool: True if logged in, False otherwise
        """
        if await self.is_logged_in():
            return True
        
        return await self.login(dealership_id)
    
    async def logout(self):
        """
        Log out from vAuto.
        
        Returns:
            bool: True if logout successful, False otherwise
        """
        logger.info("Logging out from vAuto")
        
        try:
            result = await self.nova_engine.execute_action(self._logout_action)
            
            if result:
                self.session_valid_until = None
                logger.info("Successfully logged out from vAuto")
            else:
                logger.error("Failed to log out from vAuto")
            
            return result
            
        except Exception as e:
            logger.error(f"Error logging out from vAuto: {str(e)}")
            return False
    
    async def _logout_action(self, browser):
        """
        Internal action to perform logout.
        
        Args:
            browser: Browser instance
            
        Returns:
            bool: True if logout successful, False otherwise
        """
        try:
            # Look for user menu or account dropdown
            user_menu_selectors = [
                "//div[contains(@class, 'user-menu')]",
                "//button[contains(@class, 'user-menu')]",
                "//div[contains(@class, 'account')]",
                "//span[contains(@class, 'username')]",
                "//div[contains(@class, 'profile')]"
            ]
            
            user_menu = None
            for selector in user_menu_selectors:
                try:
                    elements = await self.nova_engine.find_elements(By.XPATH, selector, timeout=1)
                    if elements:
                        user_menu = elements[0]
                        break
                except:
                    continue
            
            if not user_menu:
                logger.warning("User menu not found, trying logout directly")
                
                # Try direct logout link
                logout_selectors = [
                    "//a[contains(text(), 'Logout')]",
                    "//a[contains(text(), 'Log out')]",
                    "//button[contains(text(), 'Logout')]",
                    "//button[contains(text(), 'Log out')]",
                    "//a[contains(@href, 'logout')]"
                ]
                
                for selector in logout_selectors:
                    try:
                        logout_button = await self.nova_engine.find_element(By.XPATH, selector, timeout=1)
                        if logout_button:
                            await self.nova_engine.click_element(logout_button)
                            
                            # Wait for login page to appear
                            login_page = await self.nova_engine.wait_for_presence(By.ID, "username", timeout=5)
                            return login_page is not None
                    except:
                        continue
                
                logger.error("Logout link not found")
                return False
            
            # Click user menu to open dropdown
            await self.nova_engine.click_element(user_menu)
            
            # Wait for dropdown to appear
            await asyncio.sleep(1)
            
            # Look for logout option
            logout_selectors = [
                "//a[contains(text(), 'Logout')]",
                "//a[contains(text(), 'Log out')]",
                "//button[contains(text(), 'Logout')]",
                "//button[contains(text(), 'Log out')]",
                "//a[contains(@href, 'logout')]",
                "//div[contains(text(), 'Logout')]"
            ]
            
            for selector in logout_selectors:
                try:
                    logout_option = await self.nova_engine.find_element(By.XPATH, selector, timeout=1)
                    if logout_option:
                        await self.nova_engine.click_element(logout_option)
                        
                        # Wait for login page to appear
                        login_page = await self.nova_engine.wait_for_presence(By.ID, "username", timeout=5)
                        return login_page is not None
                except:
                    continue
            
            logger.error("Logout option not found in user menu")
            return False
            
        except Exception as e:
            logger.error(f"Logout action failed: {str(e)}")
            return False
