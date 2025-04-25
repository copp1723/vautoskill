"""
Nova Act Engine Module for vAuto Feature Verification System

This module handles browser automation and interaction with the vAuto web interface.
It provides a foundation for other modules to navigate and interact with vAuto.

Key functionalities:
- Browser initialization and configuration
- Session management
- Navigation helpers
- Screenshot capabilities
- Error recovery
"""
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

class NovaActEngine:
    """
    Core browser automation engine for the vAuto Feature Verification System.
    Uses Selenium WebDriver to control Chrome browser interactions.
    """
    
    def __init__(self, config):
        """
        Initialize the Nova Act Engine with configuration settings.
        
        Args:
            config (dict): Configuration dictionary with browser settings
        """
        self.config = config
        self.driver = None
        self.logger = logging.getLogger('nova_act_engine')
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging for the Nova Act Engine."""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(os.path.join(log_dir, 'nova_act_engine.log'))
        file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.DEBUG)
    
    def initialize_browser(self):
        """
        Initialize and configure the Chrome browser with Selenium WebDriver.
        
        Returns:
            bool: True if browser initialization was successful, False otherwise
        """
        try:
            self.logger.info("Initializing browser")
            
            chrome_options = Options()
            
            # Add configuration options
            if self.config.get('headless', False):
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Add user profile if specified
            if self.config.get('user_data_dir'):
                chrome_options.add_argument(f"--user-data-dir={self.config['user_data_dir']}")
            
            # Initialize the Chrome driver
            service = Service(executable_path=self.config.get('chromedriver_path', 'chromedriver'))
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set default timeout
            self.driver.implicitly_wait(self.config.get('implicit_wait', 10))
            
            self.logger.info("Browser initialized successfully")
            return True
            
        except WebDriverException as e:
            self.logger.error(f"Failed to initialize browser: {str(e)}")
            return False
    
    def navigate_to(self, url):
        """
        Navigate to the specified URL.
        
        Args:
            url (str): The URL to navigate to
            
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        try:
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            return True
        except WebDriverException as e:
            self.logger.error(f"Failed to navigate to {url}: {str(e)}")
            return False
    
    def wait_for_element(self, locator, timeout=None):
        """
        Wait for an element to be present in the DOM.
        
        Args:
            locator (tuple): A tuple of (By.XXX, 'selector') for the element
            timeout (int, optional): Wait timeout in seconds. Defaults to config value.
            
        Returns:
            WebElement or None: The found element or None if not found
        """
        if timeout is None:
            timeout = self.config.get('explicit_wait', 20)
            
        try:
            self.logger.debug(f"Waiting for element: {locator}")
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return element
        except TimeoutException:
            self.logger.warning(f"Timed out waiting for element: {locator}")
            return None
    
    def wait_for_clickable(self, locator, timeout=None):
        """
        Wait for an element to be clickable.
        
        Args:
            locator (tuple): A tuple of (By.XXX, 'selector') for the element
            timeout (int, optional): Wait timeout in seconds. Defaults to config value.
            
        Returns:
            WebElement or None: The found element or None if not found
        """
        if timeout is None:
            timeout = self.config.get('explicit_wait', 20)
            
        try:
            self.logger.debug(f"Waiting for clickable element: {locator}")
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            return element
        except TimeoutException:
            self.logger.warning(f"Timed out waiting for clickable element: {locator}")
            return None
    
    def click_element(self, locator, timeout=None):
        """
        Wait for an element to be clickable, then click it.
        
        Args:
            locator (tuple): A tuple of (By.XXX, 'selector') for the element
            timeout (int, optional): Wait timeout in seconds
            
        Returns:
            bool: True if click was successful, False otherwise
        """
        element = self.wait_for_clickable(locator, timeout)
        if element:
            try:
                element.click()
                self.logger.debug(f"Clicked element: {locator}")
                return True
            except WebDriverException as e:
                self.logger.warning(f"Failed to click element {locator}: {str(e)}")
                return False
        return False
    
    def input_text(self, locator, text, clear=True, timeout=None):
        """
        Input text into an element after waiting for it.
        
        Args:
            locator (tuple): A tuple of (By.XXX, 'selector') for the element
            text (str): Text to input
            clear (bool, optional): Whether to clear the field first. Defaults to True.
            timeout (int, optional): Wait timeout in seconds
            
        Returns:
            bool: True if text input was successful, False otherwise
        """
        element = self.wait_for_element(locator, timeout)
        if element:
            try:
                if clear:
                    element.clear()
                element.send_keys(text)
                self.logger.debug(f"Input text to element: {locator}")
                return True
            except WebDriverException as e:
                self.logger.warning(f"Failed to input text to element {locator}: {str(e)}")
                return False
        return False
    
    def get_element_text(self, locator, timeout=None):
        """
        Get text from an element after waiting for it.
        
        Args:
            locator (tuple): A tuple of (By.XXX, 'selector') for the element
            timeout (int, optional): Wait timeout in seconds
            
        Returns:
            str or None: The element's text or None if element not found
        """
        element = self.wait_for_element(locator, timeout)
        if element:
            try:
                text = element.text
                self.logger.debug(f"Got text from element {locator}: {text}")
                return text
            except WebDriverException as e:
                self.logger.warning(f"Failed to get text from element {locator}: {str(e)}")
                return None
        return None
    
    def take_screenshot(self, filename=None):
        """
        Take a screenshot of the current browser window.
        
        Args:
            filename (str, optional): Filename for the screenshot. 
                If None, generates a timestamp-based filename.
                
        Returns:
            str or None: Path to the saved screenshot or None if failed
        """
        if not self.driver:
            self.logger.error("Cannot take screenshot, driver not initialized")
            return None
            
        if filename is None:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        screenshots_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'logs', 
            'screenshots'
        )
        os.makedirs(screenshots_dir, exist_ok=True)
        
        filepath = os.path.join(screenshots_dir, filename)
        
        try:
            self.driver.save_screenshot(filepath)
            self.logger.info(f"Screenshot saved to {filepath}")
            return filepath
        except WebDriverException as e:
            self.logger.error(f"Failed to take screenshot: {str(e)}")
            return None
    
    def get_elements(self, locator, timeout=None):
        """
        Find all elements matching a locator.
        
        Args:
            locator (tuple): A tuple of (By.XXX, 'selector') for the elements
            timeout (int, optional): Wait timeout in seconds
            
        Returns:
            list: List of found WebElements or empty list if none found
        """
        if timeout is None:
            timeout = self.config.get('explicit_wait', 20)
            
        try:
            self.logger.debug(f"Finding elements: {locator}")
            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located(locator)
            )
            self.logger.debug(f"Found {len(elements)} elements matching {locator}")
            return elements
        except TimeoutException:
            self.logger.warning(f"Timed out waiting for elements: {locator}")
            return []
    
    def is_element_present(self, locator, timeout=5):
        """
        Check if an element is present on the page.
        
        Args:
            locator (tuple): A tuple of (By.XXX, 'selector') for the element
            timeout (int, optional): Wait timeout in seconds. Defaults to 5.
            
        Returns:
            bool: True if element is present, False otherwise
        """
        try:
            self.wait_for_element(locator, timeout)
            return True
        except TimeoutException:
            return False
    
    def execute_script(self, script, *args):
        """
        Execute JavaScript in the current browser context.
        
        Args:
            script (str): JavaScript to execute
            *args: Arguments to pass to the script
            
        Returns:
            Any: Result of the JavaScript execution
        """
        try:
            self.logger.debug(f"Executing script: {script[:50]}...")
            return self.driver.execute_script(script, *args)
        except WebDriverException as e:
            self.logger.error(f"Failed to execute script: {str(e)}")
            return None
    
    def refresh_page(self):
        """
        Refresh the current page.
        
        Returns:
            bool: True if refresh was successful, False otherwise
        """
        try:
            self.driver.refresh()
            self.logger.debug("Page refreshed")
            return True
        except WebDriverException as e:
            self.logger.error(f"Failed to refresh page: {str(e)}")
            return False
    
    def close_browser(self):
        """
        Close the browser and clean up resources.
        
        Returns:
            bool: True if close was successful, False otherwise
        """
        if not self.driver:
            return True
            
        try:
            self.logger.info("Closing browser")
            self.driver.quit()
            self.driver = None
            return True
        except WebDriverException as e:
            self.logger.error(f"Failed to close browser: {str(e)}")
            return False
    
    def __del__(self):
        """Destructor to ensure browser is closed when object is garbage collected."""
        self.close_browser()
