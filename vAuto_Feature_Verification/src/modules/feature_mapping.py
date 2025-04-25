"""
Feature Mapping Module for vAuto Feature Verification System

This module handles the mapping between window sticker feature text and vAuto checkbox names.
It implements fuzzy matching and confidence scoring to determine the best matches.

Key functionalities:
- Text normalization
- Exact matching
- Fuzzy string matching with Levenshtein distance
- Confidence scoring
- Category-based boosting
- Dealership-specific overrides
"""

import json
import logging
import re
from difflib import SequenceMatcher
import os

class FeatureMappingModule:
    """
    Maps window sticker feature text to vAuto checkbox names.
    """
    
    def __init__(self, config):
        """
        Initialize the Feature Mapping Module with configuration settings.
        
        Args:
            config (dict): Configuration dictionary with feature mapping settings
        """
        self.config = config
        self.logger = logging.getLogger('feature_mapping')
        
        # Load feature mapping dictionary
        self.mapping_dict = self._load_feature_mappings()
        
        # Load dealership-specific overrides if available
        self.dealership_overrides = self._load_dealership_overrides()
        
        # Set confidence threshold from config or default
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        
        # Set category boosts from config or defaults
        self.category_boosts = self.config.get('category_boosts', {
            'Convenience': 0.1,
            'Safety': 0.1,
            'Technology': 0.05,
            'Performance': 0.05,
            'Exterior': 0.05,
            'Interior': 0.05
        })
    
    def _load_feature_mappings(self):
        """
        Load feature mapping dictionary from configuration.
        
        Returns:
            dict: Dictionary mapping feature text patterns to checkbox names
        """
        mapping_file = self.config.get('mapping_file')
        
        if not mapping_file:
            self.logger.warning("No mapping file specified in config, using empty mapping")
            return {}
            
        try:
            with open(mapping_file, 'r') as f:
                mappings = json.load(f)
            
            self.logger.info(f"Loaded {len(mappings)} feature mappings from {mapping_file}")
            return mappings
        except (IOError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to load feature mappings from {mapping_file}: {str(e)}")
            return {}
    
    def _load_dealership_overrides(self):
        """
        Load dealership-specific overrides from configuration.
        
        Returns:
            dict: Dictionary of dealership-specific overrides
        """
        override_file = self.config.get('dealership_override_file')
        dealership_id = self.config.get('dealership_id')
        
        if not override_file or not dealership_id:
            return {}
            
        try:
            with open(override_file, 'r') as f:
                all_overrides = json.load(f)
            
            # Get overrides for this specific dealership
            dealership_overrides = all_overrides.get(dealership_id, {})
            
            self.logger.info(f"Loaded {len(dealership_overrides)} dealership-specific overrides")
            return dealership_overrides
        except (IOError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to load dealership overrides: {str(e)}")
            return {}
    
    def normalize_text(self, text):
        """
        Normalize text for comparison.
        
        Args:
            text (str): Text to normalize
            
        Returns:
            str: Normalized text
        """
        if not text:
            return ""
            
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove special characters
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Replace multiple spaces with a single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Strip leading/trailing whitespace
        normalized = normalized.strip()
        
        return normalized
    
    def calculate_similarity(self, text1, text2):
        """
        Calculate similarity score between two texts using SequenceMatcher.
        
        Args:
            text1 (str): First text
            text2 (str): Second text
            
        Returns:
            float: Similarity score between 0 and 1
        """
        # Normalize both texts
        norm_text1 = self.normalize_text(text1)
        norm_text2 = self.normalize_text(text2)
        
        # Use SequenceMatcher for similarity calculation
        matcher = SequenceMatcher(None, norm_text1, norm_text2)
        return matcher.ratio()
    
    def get_category_boost(self, feature_text):
        """
        Get category boost based on feature text.
        
        Args:
            feature_text (str): Feature text to check for category indicators
            
        Returns:
            float: Boost value between 0 and 1
        """
        normalized_text = self.normalize_text(feature_text)
        
        for category, boost in self.category_boosts.items():
            if category.lower() in normalized_text:
                self.logger.debug(f"Applied category boost {boost} for category '{category}'")
                return boost
                
        return 0.0
    
    def check_dealership_override(self, feature_text):
        """
        Check if there's a dealership-specific override for this feature.
        
        Args:
            feature_text (str): Feature text to check
            
        Returns:
            tuple or None: (checkbox_name, 1.0) if override exists, None otherwise
        """
        normalized_text = self.normalize_text(feature_text)
        
        for pattern, checkbox in self.dealership_overrides.items():
            if pattern.lower() in normalized_text:
                self.logger.info(f"Applied dealership override: '{pattern}' -> '{checkbox}'")
                return checkbox, 1.0  # Override has maximum confidence
                
        return None
    
    def map_feature(self, feature_text):
        """
        Map a feature text to a vAuto checkbox name.
        
        Args:
            feature_text (str): Feature text from window sticker
            
        Returns:
            tuple or None: (checkbox_name, confidence) or None if no mapping found
        """
        if not feature_text:
            return None
            
        self.logger.debug(f"Mapping feature: '{feature_text}'")
        
        # Check dealership overrides first
        override = self.check_dealership_override(feature_text)
        if override:
            return override
            
        normalized_text = self.normalize_text(feature_text)
        
        # Try exact match first (case-insensitive)
        for pattern, checkbox in self.mapping_dict.items():
            if self.normalize_text(pattern) == normalized_text:
                self.logger.debug(f"Exact match found: '{pattern}' -> '{checkbox}'")
                return checkbox, 1.0
        
        # If no exact match, try fuzzy matching
        best_match = None
        best_score = 0.0
        
        for pattern, checkbox in self.mapping_dict.items():
            similarity = self.calculate_similarity(pattern, normalized_text)
            
            # Apply category boost if applicable
            category_boost = self.get_category_boost(feature_text)
            boosted_similarity = min(1.0, similarity + category_boost)
            
            if boosted_similarity > best_score:
                best_score = boosted_similarity
                best_match = checkbox
                
        # Return best match if confidence is above threshold
        if best_match and best_score >= self.confidence_threshold:
            self.logger.debug(f"Fuzzy match found: '{feature_text}' -> '{best_match}' (confidence: {best_score:.2f})")
            return best_match, best_score
            
        self.logger.debug(f"No match found for: '{feature_text}' (best confidence: {best_score:.2f})")
        return None
    
    def bulk_map_features(self, feature_list):
        """
        Map a list of features to vAuto checkbox names.
        
        Args:
            feature_list (list): List of feature texts from window sticker
            
        Returns:
            dict: Dictionary mapping checkbox names to their confidence scores
        """
        mapped_features = {}
        
        for feature in feature_list:
            result = self.map_feature(feature)
            if result:
                checkbox, confidence = result
                
                # Only keep the highest confidence for each checkbox
                if checkbox not in mapped_features or confidence > mapped_features[checkbox]:
                    mapped_features[checkbox] = confidence
        
        return mapped_features
    
    def get_high_confidence_features(self, mapped_features, min_confidence=None):
        """
        Get a list of checkbox names with confidence above threshold.
        
        Args:
            mapped_features (dict): Dictionary mapping checkbox names to confidence scores
            min_confidence (float, optional): Minimum confidence threshold.
                If None, use the default threshold.
                
        Returns:
            list: List of checkbox names with confidence above threshold
        """
        if min_confidence is None:
            min_confidence = self.confidence_threshold
            
        high_confidence = []
        
        for checkbox, confidence in mapped_features.items():
            if confidence >= min_confidence:
                high_confidence.append(checkbox)
                
        return high_confidence
