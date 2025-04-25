"""
Window Sticker Processing Module for vAuto Feature Verification System

This module handles extracting and processing window sticker information, including:
- Navigating to the Factory Equipment tab
- Extracting window sticker content
- Parsing feature sections
- Extracting feature list
- Handling different sticker formats
"""

import logging
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class WindowStickerProcessingModule:
    """
    Handles extraction and processing of window sticker information.
    """
    
    # Define selectors for factory equipment tab and window sticker elements
    FACTORY_EQUIPMENT_TAB = (By.CSS_SELECTOR, ".factory-equipment-tab")  # Replace with actual selector
    WINDOW_STICKER_CONTAINER = (By.CSS_SELECTOR, ".window-sticker-container")  # Replace with actual selector
    FEATURE_SECTIONS = (By.CSS_SELECTOR, ".feature-section")  # Replace with actual selector
    FEATURE_SECTION_TITLE = (By.CSS_SELECTOR, ".section-title")  # Replace with actual selector
    FEATURE_ITEMS = (By.CSS_SELECTOR, ".feature-item")  # Replace with actual selector
    
    # Common feature categories
    FEATURE_CATEGORIES = [
        "Standard Equipment",
        "Optional Equipment",
        "Factory Installed Options",
        "Convenience Features",
        "Safety Features",
        "Performance Features",
        "Comfort Features",
        "Technology Features",
        "Exterior Features",
        "Interior Features",
        "Handling Features"
    ]
    
    def __init__(self, nova_engine, feature_mapping_module, config):
        """
        Initialize the Window Sticker Processing Module.
        
        Args:
            nova_engine: Initialized NovaActEngine instance
            feature_mapping_module: Feature mapping module for text matching
            config (dict): Configuration dictionary with window sticker settings
        """
        self.nova = nova_engine
        self.feature_mapping = feature_mapping_module
        self.config = config
        self.logger = logging.getLogger('window_sticker_processing')
    
    def navigate_to_factory_equipment(self, vehicle_url):
        """
        Navigate to the Factory Equipment tab for a vehicle.
        
        Args:
            vehicle_url (str): URL of the vehicle detail page
            
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        self.logger.info(f"Navigating to factory equipment tab for vehicle: {vehicle_url}")
        
        # Navigate to vehicle detail page
        if not self.nova.navigate_to(vehicle_url):
            self.logger.error(f"Failed to navigate to vehicle detail page: {vehicle_url}")
            return False
        
        # Click on Factory Equipment tab
        if not self.nova.click_element(self.FACTORY_EQUIPMENT_TAB):
            self.logger.error("Failed to click Factory Equipment tab")
            return False
        
        # Verify window sticker container is present
        if not self.nova.wait_for_element(self.WINDOW_STICKER_CONTAINER):
            self.logger.error("Window sticker container not found")
            return False
        
        self.logger.info("Successfully navigated to factory equipment tab")
        return True
    
    def extract_window_sticker_content(self):
        """
        Extract the full window sticker content.
        
        Returns:
            dict: Dictionary with feature sections and their items
        """
        self.logger.info("Extracting window sticker content")
        
        # Check if window sticker container is present
        sticker_container = self.nova.wait_for_element(self.WINDOW_STICKER_CONTAINER)
        if not sticker_container:
            self.logger.error("Window sticker container not found")
            return {}
        
        # Get all feature sections
        feature_sections = self.nova.get_elements(self.FEATURE_SECTIONS)
        
        if not feature_sections:
            self.logger.warning("No feature sections found in window sticker")
            
            # Attempt to get all text as a fallback
            sticker_text = sticker_container.text
            if sticker_text:
                self.logger.info("Retrieved window sticker text as plain text")
                return self._parse_plain_text_sticker(sticker_text)
            else:
                self.logger.error("Window sticker content is empty")
                return {}
        
        # Process each feature section
        sticker_content = {}
        
        for section in feature_sections:
            try:
                # Get section title
                title_elem = section.find_element(*self.FEATURE_SECTION_TITLE)
                section_title = title_elem.text.strip()
                
                # Get feature items
                feature_elems = section.find_elements(*self.FEATURE_ITEMS)
                features = [elem.text.strip() for elem in feature_elems if elem.text.strip()]
                
                # Add to content dictionary
                if section_title and features:
                    sticker_content[section_title] = features
                    self.logger.debug(f"Extracted section '{section_title}' with {len(features)} features")
                
            except NoSuchElementException as e:
                self.logger.warning(f"Error extracting a feature section: {str(e)}")
                continue
        
        self.logger.info(f"Extracted {len(sticker_content)} feature sections from window sticker")
        return sticker_content
    
    def _parse_plain_text_sticker(self, text):
        """
        Parse window sticker content from plain text when structured sections are not available.
        
        Args:
            text (str): Raw text from window sticker
            
        Returns:
            dict: Dictionary with feature sections and their items
        """
        self.logger.info("Parsing window sticker from plain text")
        
        sticker_content = {}
        current_section = "General Features"
        current_features = []
        
        # Split text into lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            # Check if this line is a potential section title
            is_section_title = False
            
            # Check if line matches any known category name
            for category in self.FEATURE_CATEGORIES:
                if category.lower() in line.lower():
                    is_section_title = True
                    break
            
            # Check if line looks like a title (all caps, short, ends with colon)
            if not is_section_title:
                if line.isupper() or line.endswith(':'):
                    is_section_title = True
            
            if is_section_title:
                # Save previous section if it has features
                if current_features:
                    sticker_content[current_section] = current_features
                
                # Start new section
                current_section = line.rstrip(':')
                current_features = []
            else:
                # Add line as a feature to current section
                current_features.append(line)
        
        # Add the last section
        if current_features:
            sticker_content[current_section] = current_features
        
        self.logger.info(f"Parsed {len(sticker_content)} sections from plain text")
        return sticker_content
    
    def extract_all_features(self, sticker_content):
        """
        Extract a flat list of all features from the sticker content.
        
        Args:
            sticker_content (dict): Dictionary with feature sections and their items
            
        Returns:
            list: Flat list of all features
        """
        all_features = []
        
        for section, features in sticker_content.items():
            # Add section context to features if configured
            if self.config.get('include_section_context', True):
                prefixed_features = [f"{section}: {feature}" for feature in features]
                all_features.extend(prefixed_features)
            else:
                all_features.extend(features)
        
        self.logger.info(f"Extracted {len(all_features)} total features")
        return all_features
    
    def get_mapped_features(self, all_features):
        """
        Get mapped features using the feature mapping module.
        
        Args:
            all_features (list): List of features from window sticker
            
        Returns:
            dict: Dictionary mapping vAuto checkbox names to confidence scores
        """
        self.logger.info("Mapping window sticker features to vAuto checkboxes")
        
        mapped_features = {}
        
        for feature in all_features:
            # Use feature mapping module to map this feature
            mapping_result = self.feature_mapping.map_feature(feature)
            
            if mapping_result:
                checkbox_name, confidence = mapping_result
                
                # Only keep the highest confidence for each checkbox
                if checkbox_name not in mapped_features or confidence > mapped_features[checkbox_name]:
                    mapped_features[checkbox_name] = confidence
                    self.logger.debug(f"Mapped '{feature}' to '{checkbox_name}' with confidence {confidence}")
        
        self.logger.info(f"Mapped {len(mapped_features)} unique vAuto checkboxes")
        return mapped_features
    
    def get_high_confidence_features(self, mapped_features, min_confidence=0.7):
        """
        Filter mapped features to get only those with high confidence.
        
        Args:
            mapped_features (dict): Dictionary mapping checkbox names to confidence scores
            min_confidence (float, optional): Minimum confidence threshold. Defaults to 0.7.
            
        Returns:
            list: List of checkbox names with confidence above threshold
        """
        high_confidence = [
            checkbox for checkbox, confidence in mapped_features.items()
            if confidence >= min_confidence
        ]
        
        self.logger.info(f"Found {len(high_confidence)} features with confidence >= {min_confidence}")
        return high_confidence
    
    def process_vehicle_window_sticker(self, vehicle_url):
        """
        Process complete window sticker workflow for a vehicle.
        
        Args:
            vehicle_url (str): URL of the vehicle detail page
            
        Returns:
            tuple: (mapped_features, high_confidence_features) or (None, None) if failed
        """
        self.logger.info(f"Processing window sticker for vehicle: {vehicle_url}")
        
        # Navigate to factory equipment tab
        if not self.navigate_to_factory_equipment(vehicle_url):
            self.logger.error("Failed to navigate to factory equipment tab")
            return None, None
        
        # Extract window sticker content
        sticker_content = self.extract_window_sticker_content()
        if not sticker_content:
            self.logger.error("Failed to extract window sticker content")
            return None, None
        
        # Extract all features
        all_features = self.extract_all_features(sticker_content)
        if not all_features:
            self.logger.warning("No features found in window sticker")
            return {}, []
        
        # Map features to vAuto checkboxes
        mapped_features = self.get_mapped_features(all_features)
        
        # Get high confidence features
        high_confidence = self.get_high_confidence_features(
            mapped_features, 
            self.config.get('min_confidence', 0.7)
        )
        
        return mapped_features, high_confidence
