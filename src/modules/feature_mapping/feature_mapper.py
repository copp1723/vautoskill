"""
Feature Mapping Module for vAuto Feature Verification System.

Maps window sticker features to vAuto checkbox states using fuzzy matching.
"""

import logging
import re
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

class FeatureMappingModule:
    """
    Maps window sticker features to vAuto checkbox states.
    """
    
    @staticmethod
    def normalize_text(text):
        """
        Normalize text for comparison.
        
        Args:
            text (str): Text to normalize
            
        Returns:
            str: Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        # Replace special characters with spaces
        text = re.sub(r'[^\w\s-]', ' ', text)
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing spaces
        return text.strip()
    
    @staticmethod
    def get_similarity(feature, alternative):
        """
        Calculate similarity between two strings.
        
        Args:
            feature (str): Feature from window sticker
            alternative (str): Alternative feature name from mapping
            
        Returns:
            int: Similarity score (0-100)
        """
        normalized_feature = FeatureMappingModule.normalize_text(feature)
        normalized_alternative = FeatureMappingModule.normalize_text(alternative)
        
        # Check direct matches first (exact or substring)
        if normalized_feature == normalized_alternative:
            return 100
        
        if normalized_alternative in normalized_feature or normalized_feature in normalized_alternative:
            return 95
        
        # Calculate fuzzy match similarity
        return fuzz.ratio(normalized_feature, normalized_alternative)
    
    @staticmethod
    def map_features(window_sticker_features, feature_mapping, confidence_threshold=90):
        """
        Map window sticker features to vAuto checkbox states.
        
        Args:
            window_sticker_features (list): Features from window sticker
            feature_mapping (dict): Mapping of vAuto features to alternative names
            confidence_threshold (int, optional): Minimum similarity score to consider a match
            
        Returns:
            dict: Mapping of vAuto features to boolean values
        """
        logger.info(f"Mapping {len(window_sticker_features)} window sticker features to vAuto checkboxes")
        result = {}
        matched_features = []
        
        # Check each vAuto feature against the window sticker features
        for vauto_feature, alternatives in feature_mapping.items():
            # Find best match and similarity score
            best_match = None
            best_score = 0
            
            for feature in window_sticker_features:
                for alternative in alternatives:
                    similarity = FeatureMappingModule.get_similarity(feature, alternative)
                    
                    if similarity > best_score:
                        best_score = similarity
                        best_match = feature
            
            # Add to result if confidence threshold is met
            is_present = best_score >= confidence_threshold
            
            if is_present:
                logger.debug(f"Matched '{vauto_feature}' to '{best_match}' with score {best_score}")
                matched_features.append(best_match)
            
            result[vauto_feature] = is_present
        
        # Log features that weren't matched
        unmatched_features = [f for f in window_sticker_features if f not in matched_features]
        if unmatched_features:
            logger.warning(f"Unmatched features: {unmatched_features}")
        
        logger.info(f"Mapped {len(matched_features)} features with confidence >= {confidence_threshold}")
        return result
