"""
Inventory Discovery Module for vAuto Feature Verification System

This module handles finding and extracting vehicle inventory items in vAuto, including:
- Navigating to inventory list
- Applying filters (e.g., age filter for new vehicles)
- Extracting vehicle links
- Handling pagination
- Parsing basic vehicle information
"""

import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class InventoryDiscoveryModule:
    """
    Handles discovery and extraction of vehicle inventory in vAuto.
    """
    
    # Define selectors for inventory navigation and filtering
    INVENTORY_URL = "https://vauto.com/inventory"  # Replace with actual URL
    
    # Filters
    AGE_FILTER_DROPDOWN = (By.CSS_SELECTOR, ".age-filter-dropdown")  # Replace with actual selector
    AGE_FILTER_0_1_DAYS = (By.CSS_SELECTOR, ".age-filter-0-1")  # Replace with actual selector
    APPLY_FILTERS_BUTTON = (By.CSS_SELECTOR, ".apply-filters")  # Replace with actual selector
    
    # Inventory items
    VEHICLE_ITEMS = (By.CSS_SELECTOR, ".vehicle-item")  # Replace with actual selector
    VEHICLE_LINK = (By.CSS_SELECTOR, ".vehicle-link")  # Replace with actual selector
    VEHICLE_VIN = (By.CSS_SELECTOR, ".vehicle-vin")  # Replace with actual selector
    VEHICLE_STOCK = (By.CSS_SELECTOR, ".vehicle-stock")  # Replace with actual selector
    VEHICLE_YEAR = (By.CSS_SELECTOR, ".vehicle-year")  # Replace with actual selector
    VEHICLE_MAKE = (By.CSS_SELECTOR, ".vehicle-make")  # Replace with actual selector
    VEHICLE_MODEL = (By.CSS_SELECTOR, ".vehicle-model")  # Replace with actual selector
    
    # Pagination
    NEXT_PAGE_BUTTON = (By.CSS_SELECTOR, ".pagination-next")  # Replace with actual selector
    PAGE_INDICATOR = (By.CSS_SELECTOR, ".page-indicator")  # Replace with actual selector
    
    def __init__(self, nova_engine, config):
        """
        Initialize the Inventory Discovery Module.
        
        Args:
            nova_engine: Initialized NovaActEngine instance
            config (dict): Configuration dictionary with inventory settings
        """
        self.nova = nova_engine
        self.config = config
        self.logger = logging.getLogger('inventory_discovery')
    
    def navigate_to_inventory(self):
        """
        Navigate to the inventory list page.
        
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        self.logger.info("Navigating to inventory list")
        return self.nova.navigate_to(self.INVENTORY_URL)
    
    def apply_age_filter(self):
        """
        Apply age filter to show only recent vehicles (0-1 days).
        
        Returns:
            bool: True if filter was applied successfully, False otherwise
        """
        self.logger.info("Applying age filter (0-1 days)")
        
        # Click age filter dropdown
        if not self.nova.click_element(self.AGE_FILTER_DROPDOWN):
            self.logger.error("Failed to click age filter dropdown")
            return False
        
        # Select 0-1 days option
        if not self.nova.click_element(self.AGE_FILTER_0_1_DAYS):
            self.logger.error("Failed to select 0-1 days filter")
            return False
        
        # Click apply filters if there's a separate button
        if self.nova.is_element_present(self.APPLY_FILTERS_BUTTON):
            if not self.nova.click_element(self.APPLY_FILTERS_BUTTON):
                self.logger.error("Failed to click apply filters button")
                return False
        
        # Wait for page to reload with filtered results
        time.sleep(2)
        
        self.logger.info("Age filter applied successfully")
        return True
    
    def get_vehicles_on_current_page(self):
        """
        Extract vehicle information from the current page.
        
        Returns:
            list: List of dictionaries containing vehicle information
        """
        self.logger.info("Extracting vehicles from current page")
        
        vehicles = []
        
        # Get all vehicle items on the page
        vehicle_elements = self.nova.get_elements(self.VEHICLE_ITEMS)
        
        if not vehicle_elements:
            self.logger.warning("No vehicle items found on current page")
            return vehicles
        
        self.logger.info(f"Found {len(vehicle_elements)} vehicles on current page")
        
        # Extract information for each vehicle
        for vehicle_elem in vehicle_elements:
            try:
                # Get the link to the vehicle detail page
                link_elem = vehicle_elem.find_element(*self.VEHICLE_LINK)
                detail_url = link_elem.get_attribute('href')
                
                # Extract basic vehicle info
                vin = self._get_text_from_element(vehicle_elem, self.VEHICLE_VIN)
                stock = self._get_text_from_element(vehicle_elem, self.VEHICLE_STOCK)
                year = self._get_text_from_element(vehicle_elem, self.VEHICLE_YEAR)
                make = self._get_text_from_element(vehicle_elem, self.VEHICLE_MAKE)
                model = self._get_text_from_element(vehicle_elem, self.VEHICLE_MODEL)
                
                vehicle_info = {
                    'detail_url': detail_url,
                    'vin': vin,
                    'stock': stock,
                    'year': year,
                    'make': make,
                    'model': model
                }
                
                vehicles.append(vehicle_info)
                
            except NoSuchElementException as e:
                self.logger.warning(f"Failed to extract complete info for a vehicle: {str(e)}")
                continue
        
        return vehicles
    
    def _get_text_from_element(self, parent_element, locator):
        """
        Helper to get text from an element within a parent element.
        
        Args:
            parent_element: Parent WebElement
            locator (tuple): Locator tuple (By.XXX, 'selector')
            
        Returns:
            str: Text content or empty string if not found
        """
        try:
            element = parent_element.find_element(*locator)
            return element.text.strip()
        except NoSuchElementException:
            return ""
    
    def has_next_page(self):
        """
        Check if there is a next page of inventory results.
        
        Returns:
            bool: True if next page exists, False otherwise
        """
        # Check if the next page button exists and is enabled
        next_button = self.nova.wait_for_element(self.NEXT_PAGE_BUTTON, timeout=2)
        if not next_button:
            return False
            
        # Check if the button is disabled
        disabled = next_button.get_attribute('disabled')
        if disabled:
            return False
            
        return True
    
    def go_to_next_page(self):
        """
        Navigate to the next page of inventory results.
        
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        if not self.has_next_page():
            self.logger.info("No next page available")
            return False
            
        # Get current page number for logging
        current_page = self._get_current_page_number()
        
        # Click next page button
        if not self.nova.click_element(self.NEXT_PAGE_BUTTON):
            self.logger.error("Failed to click next page button")
            return False
            
        # Wait for page to load
        time.sleep(2)
        
        # Verify page changed
        new_page = self._get_current_page_number()
        if new_page and current_page and new_page > current_page:
            self.logger.info(f"Navigated to page {new_page}")
            return True
        else:
            self.logger.warning(f"Failed to verify page change: {current_page} -> {new_page}")
            # Even if we can't verify, assume it worked if we were able to click
            return True
    
    def _get_current_page_number(self):
        """
        Get the current page number from the page indicator.
        
        Returns:
            int or None: Current page number or None if not found
        """
        page_indicator = self.nova.wait_for_element(self.PAGE_INDICATOR, timeout=2)
        if not page_indicator:
            return None
            
        try:
            # Assuming the page indicator has text like "Page 2 of 5"
            indicator_text = page_indicator.text.strip()
            # Extract the page number using string methods or regex
            parts = indicator_text.split()
            if len(parts) >= 2 and parts[0].lower() == 'page':
                return int(parts[1])
            return None
        except (ValueError, IndexError):
            self.logger.warning(f"Failed to parse page number from '{indicator_text}'")
            return None
    
    def discover_vehicles(self, max_pages=None):
        """
        Discover all vehicles meeting the filter criteria.
        
        Args:
            max_pages (int, optional): Maximum number of pages to process.
                If None, process all pages.
                
        Returns:
            list: List of dictionaries containing vehicle information
        """
        self.logger.info("Starting vehicle discovery process")
        
        # Navigate to inventory page
        if not self.navigate_to_inventory():
            self.logger.error("Failed to navigate to inventory page")
            return []
        
        # Apply age filter
        if not self.apply_age_filter():
            self.logger.warning("Failed to apply age filter, proceeding with default view")
        
        all_vehicles = []
        page_count = 0
        
        # Process each page
        while True:
            page_count += 1
            self.logger.info(f"Processing page {page_count}")
            
            # Get vehicles on current page
            vehicles = self.get_vehicles_on_current_page()
            all_vehicles.extend(vehicles)
            
            # Check if we've reached the maximum pages
            if max_pages and page_count >= max_pages:
                self.logger.info(f"Reached maximum pages ({max_pages}), stopping")
                break
                
            # Check if there's a next page
            if not self.has_next_page():
                self.logger.info("No more pages available")
                break
                
            # Go to next page
            if not self.go_to_next_page():
                self.logger.error("Failed to navigate to next page")
                break
            
            # Optional: add a small delay between pages
            time.sleep(1)
        
        self.logger.info(f"Discovery complete. Found {len(all_vehicles)} vehicles across {page_count} pages")
        return all_vehicles
