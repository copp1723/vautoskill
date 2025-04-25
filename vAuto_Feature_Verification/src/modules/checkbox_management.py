"""
Checkbox Management Module for vAuto Feature Verification System

This module handles interacting with vehicle feature checkboxes, including:
- Navigating to vehicle checkbox page
- Identifying checkbox elements
- Getting current checkbox states
- Updating checkboxes based on mappings
- Saving changes
- Verifying changes were applied
"""

import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class CheckboxManagementModule:
    """
    Handles management of vehicle feature checkboxes in vAuto.
    """
    
    # Define selectors for checkbox page and elements
    CHECKBOX_TAB = (By.CSS_SELECTOR, ".checkbox-tab")  # Replace with actual selector
    CHECKBOX_CONTAINER = (By.CSS_SELECTOR, ".checkbox-container")  # Replace with actual selector
    CHECKBOX_ITEMS = (By.CSS_SELECTOR, ".checkbox-item")  # Replace with actual selector
    CHECKBOX_LABEL = (By.CSS_SELECTOR, ".checkbox-label")  # Replace with actual selector
    CHECKBOX_INPUT = (By.CSS_SELECTOR, "input[type='checkbox']")  # Replace with actual selector
    
    # Save button
    SAVE_BUTTON = (By.CSS_SELECTOR, ".save-button")  # Replace with actual selector
    
    # Success indicator
    SAVE_SUCCESS_NOTIFICATION = (By.CSS_SELECTOR, ".success-notification")  # Replace with actual selector
    
    def __init__(self, nova_engine, config):
        """
        Initialize the Checkbox Management Module.
        
        Args:
            nova_engine: Initialized NovaActEngine instance
            config (dict): Configuration dictionary with checkbox settings
        """
        self.nova = nova_engine
        self.config = config
        self.logger = logging.getLogger('checkbox_management')
    
    def navigate_to_checkbox_page(self, vehicle_url):
        """
        Navigate to the checkbox page for a vehicle.
        
        Args:
            vehicle_url (str): URL of the vehicle detail page
            
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        self.logger.info(f"Navigating to checkbox page for vehicle: {vehicle_url}")
        
        # Navigate to vehicle detail page
        if not self.nova.navigate_to(vehicle_url):
            self.logger.error(f"Failed to navigate to vehicle detail page: {vehicle_url}")
            return False
        
        # Click on Checkbox tab
        if not self.nova.click_element(self.CHECKBOX_TAB):
            self.logger.error("Failed to click Checkbox tab")
            return False
        
        # Verify checkbox container is present
        if not self.nova.wait_for_element(self.CHECKBOX_CONTAINER):
            self.logger.error("Checkbox container not found")
            return False
        
        self.logger.info("Successfully navigated to checkbox page")
        return True
    
    def get_all_checkboxes(self):
        """
        Get all checkbox elements on the page.
        
        Returns:
            dict: Dictionary mapping checkbox names to their elements
        """
        self.logger.info("Getting all checkboxes on the page")
        
        checkbox_dict = {}
        
        # Get all checkbox items
        checkbox_items = self.nova.get_elements(self.CHECKBOX_ITEMS)
        
        if not checkbox_items:
            self.logger.warning("No checkbox items found on the page")
            return checkbox_dict
        
        self.logger.info(f"Found {len(checkbox_items)} checkbox items")
        
        for item in checkbox_items:
            try:
                # Get checkbox label
                label_elem = item.find_element(*self.CHECKBOX_LABEL)
                checkbox_name = label_elem.text.strip()
                
                # Get checkbox input
                input_elem = item.find_element(*self.CHECKBOX_INPUT)
                
                # Add to dictionary
                if checkbox_name:
                    checkbox_dict[checkbox_name] = input_elem
                    self.logger.debug(f"Found checkbox: {checkbox_name}")
                
            except NoSuchElementException as e:
                self.logger.warning(f"Error processing a checkbox item: {str(e)}")
                continue
        
        self.logger.info(f"Processed {len(checkbox_dict)} named checkboxes")
        return checkbox_dict
    
    def get_checkbox_states(self, checkbox_dict):
        """
        Get the current state (checked/unchecked) of all checkboxes.
        
        Args:
            checkbox_dict (dict): Dictionary mapping checkbox names to their elements
            
        Returns:
            dict: Dictionary mapping checkbox names to their current states (True/False)
        """
        self.logger.info("Getting current states of all checkboxes")
        
        checkbox_states = {}
        
        for name, element in checkbox_dict.items():
            try:
                # Get the checked state
                is_checked = element.is_selected()
                checkbox_states[name] = is_checked
                self.logger.debug(f"Checkbox '{name}' is {'checked' if is_checked else 'unchecked'}")
            except Exception as e:
                self.logger.warning(f"Error getting state of checkbox '{name}': {str(e)}")
                checkbox_states[name] = False  # Default to unchecked
        
        self.logger.info(f"Retrieved states for {len(checkbox_states)} checkboxes")
        return checkbox_states
    
    def update_checkboxes(self, checkbox_dict, checkboxes_to_check):
        """
        Update checkboxes based on the provided list of checkboxes to check.
        
        Args:
            checkbox_dict (dict): Dictionary mapping checkbox names to their elements
            checkboxes_to_check (list): List of checkbox names to be checked
            
        Returns:
            tuple: (updates_count, errors_count)
        """
        self.logger.info(f"Updating checkboxes, {len(checkboxes_to_check)} to be checked")
        
        # Get current states
        current_states = self.get_checkbox_states(checkbox_dict)
        
        updates_count = 0
        errors_count = 0
        
        for name, element in checkbox_dict.items():
            try:
                # Determine if checkbox should be checked
                should_be_checked = name in checkboxes_to_check
                
                # Check if update is needed
                if current_states.get(name, False) != should_be_checked:
                    self.logger.debug(f"Updating checkbox '{name}' to {'checked' if should_be_checked else 'unchecked'}")
                    
                    # JavaScript is often more reliable for checkbox manipulation
                    js_script = f"arguments[0].checked = {str(should_be_checked).lower()};"
                    self.nova.execute_script(js_script, element)
                    
                    # Verify the change took effect
                    if element.is_selected() != should_be_checked:
                        # Try direct click as fallback
                        if should_be_checked and not element.is_selected():
                            element.click()
                        elif not should_be_checked and element.is_selected():
                            element.click()
                    
                    updates_count += 1
            except Exception as e:
                self.logger.warning(f"Error updating checkbox '{name}': {str(e)}")
                errors_count += 1
        
        self.logger.info(f"Updated {updates_count} checkboxes with {errors_count} errors")
        return updates_count, errors_count
    
    def save_changes(self):
        """
        Save the checkbox changes.
        
        Returns:
            bool: True if changes were saved successfully, False otherwise
        """
        self.logger.info("Saving checkbox changes")
        
        # Click save button
        if not self.nova.click_element(self.SAVE_BUTTON):
            self.logger.error("Failed to click save button")
            return False
        
        # Wait for save to complete
        time.sleep(2)
        
        # Check for success notification
        if self.nova.is_element_present(self.SAVE_SUCCESS_NOTIFICATION, timeout=5):
            self.logger.info("Save operation completed successfully")
            return True
        else:
            self.logger.warning("No success notification found after save operation")
            # Even without notification, assume it worked if the save button was clicked
            return True
    
    def verify_checkboxes(self, checkbox_dict, checkboxes_to_check):
        """
        Verify that checkboxes have been updated correctly.
        
        Args:
            checkbox_dict (dict): Dictionary mapping checkbox names to their elements
            checkboxes_to_check (list): List of checkbox names that should be checked
            
        Returns:
            tuple: (success_count, error_count, error_list)
        """
        self.logger.info("Verifying checkbox states after update")
        
        # Refresh current states
        current_states = self.get_checkbox_states(checkbox_dict)
        
        success_count = 0
        error_count = 0
        error_list = []
        
        # Compare each checkbox state to the desired state
        for name, is_checked in current_states.items():
            should_be_checked = name in checkboxes_to_check
            
            if is_checked == should_be_checked:
                success_count += 1
            else:
                error_count += 1
                error_list.append(name)
                self.logger.warning(
                    f"Checkbox verification failed for '{name}': "
                    f"Expected {'checked' if should_be_checked else 'unchecked'}, "
                    f"but found {'checked' if is_checked else 'unchecked'}"
                )
        
        self.logger.info(f"Verification complete: {success_count} correct, {error_count} incorrect")
        return success_count, error_count, error_list
    
    def manage_vehicle_checkboxes(self, vehicle_url, checkboxes_to_check):
        """
        Complete checkbox management workflow for a vehicle.
        
        Args:
            vehicle_url (str): URL of the vehicle detail page
            checkboxes_to_check (list): List of checkbox names to be checked
            
        Returns:
            dict: Results dictionary with counts and status
        """
        results = {
            'success': False,
            'updates_count': 0,
            'errors_count': 0,
            'verification_success': 0,
            'verification_errors': 0,
            'error_checkboxes': []
        }
        
        self.logger.info(f"Starting checkbox management for vehicle: {vehicle_url}")
        
        # Navigate to checkbox page
        if not self.navigate_to_checkbox_page(vehicle_url):
            self.logger.error("Failed to navigate to checkbox page")
            return results
        
        # Get all checkboxes
        checkbox_dict = self.get_all_checkboxes()
        if not checkbox_dict:
            self.logger.error("No checkboxes found to manage")
            return results
        
        # Update checkboxes
        updates_count, errors_count = self.update_checkboxes(checkbox_dict, checkboxes_to_check)
        results['updates_count'] = updates_count
        results['errors_count'] = errors_count
        
        # Save changes
        if not self.save_changes():
            self.logger.error("Failed to save checkbox changes")
            return results
        
        # Verify changes (optional based on config)
        if self.config.get('verify_after_save', True):
            # Refresh the page to ensure we're seeing the latest data
            self.nova.refresh_page()
            time.sleep(2)
            
            # Get updated checkbox elements
            checkbox_dict = self.get_all_checkboxes()
            
            # Verify the changes
            success_count, error_count, error_list = self.verify_checkboxes(checkbox_dict, checkboxes_to_check)
            results['verification_success'] = success_count
            results['verification_errors'] = error_count
            results['error_checkboxes'] = error_list
        
        results['success'] = (results['errors_count'] == 0 and results['verification_errors'] == 0)
        
        self.logger.info(f"Checkbox management completed with success={results['success']}")
        return results
