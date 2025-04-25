"""
Workflow Orchestration Module for vAuto Feature Verification System.

Handles:
- Single dealership workflow
- Vehicle processing queue
- Basic scheduling
- Session timeout handling
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WorkflowModule:
    """
    Module for orchestrating the vAuto feature verification workflow.
    """
    
    def __init__(self, nova_engine, config):
        """
        Initialize the workflow module.
        
        Args:
            nova_engine (NovaActEngine): Nova Act Engine instance
            config (dict): System configuration
        """
        self.nova_engine = nova_engine
        self.config = config
        self.modules = {}
        self.processing_stats = {
            'vehicles_processed': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'features_found': 0,
            'features_mapped': 0,
            'checkboxes_updated': 0
        }
    
    def register_module(self, name, module):
        """
        Register a module with the workflow.
        
        Args:
            name (str): Module name
            module (object): Module instance
        """
        self.modules[name] = module
        logger.info(f"Registered module: {name}")
    
    async def run_workflow(self, dealer_config):
        """
        Run the complete workflow for a single dealership.
        
        Args:
            dealer_config (dict): Dealer configuration
            
        Returns:
            dict: Processing statistics
        """
        logger.info(f"Starting workflow for dealership: {dealer_config['name']}")
        
        start_time = datetime.now()
        self._reset_stats()
        
        try:
            # Authenticate
            await self._authenticate(dealer_config)
            
            # Discover inventory
            vehicle_urls = await self._discover_inventory(dealer_config)
            
            # Process vehicles
            await self._process_vehicles(vehicle_urls, dealer_config)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() / 60
            self.processing_stats['processing_time_minutes'] = processing_time
            
            # Log workflow completion
            logger.info(f"Workflow completed for {dealer_config['name']} in {processing_time:.2f} minutes")
            logger.info(f"Processed {self.processing_stats['vehicles_processed']} vehicles with "
                      f"{self.processing_stats['successful_updates']} successful updates and "
                      f"{self.processing_stats['failed_updates']} failed updates")
            
            return self.processing_stats
            
        except Exception as e:
            logger.error(f"Workflow failed for {dealer_config['name']}: {str(e)}")
            self.processing_stats['error'] = str(e)
            return self.processing_stats
        finally:
            # Ensure browser is closed
            await self.nova_engine.close_browser()
    
    def _reset_stats(self):
        """
        Reset processing statistics.
        """
        self.processing_stats = {
            'vehicles_processed': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'features_found': 0,
            'features_mapped': 0,
            'checkboxes_updated': 0,
            'start_time': datetime.now().isoformat(),
        }
    
    async def _authenticate(self, dealer_config):
        """
        Authenticate to vAuto.
        
        Args:
            dealer_config (dict): Dealer configuration
        """
        logger.info(f"Authenticating for dealership: {dealer_config['name']}")
        
        auth_module = self.modules.get('authentication')
        if not auth_module:
            raise ValueError("Authentication module not registered")
        
        # Create authentication config
        auth_config = {
            'credentials': dealer_config['credentials']
        }
        
        # Initialize browser and authenticate
        await self.nova_engine.initialize_browser()
        await auth_module.authenticate(await self.nova_engine.ensure_browser(), auth_config)
        
        logger.info("Authentication successful")
    
    async def _discover_inventory(self, dealer_config):
        """
        Discover inventory for the dealership.
        
        Args:
            dealer_config (dict): Dealer configuration
            
        Returns:
            list: List of vehicle URLs
        """
        logger.info(f"Discovering inventory for dealership: {dealer_config['name']}")
        
        inventory_module = self.modules.get('inventory_discovery')
        if not inventory_module:
            raise ValueError("Inventory discovery module not registered")
        
        # Discover inventory
        vehicle_urls = await inventory_module.discover_inventory(dealer_config)
        
        # Apply vehicle limit if specified
        max_vehicles = self.config['processing']['max_vehicles_per_batch']
        if max_vehicles > 0 and len(vehicle_urls) > max_vehicles:
            logger.info(f"Limiting to {max_vehicles} vehicles out of {len(vehicle_urls)} discovered")
            vehicle_urls = vehicle_urls[:max_vehicles]
        
        logger.info(f"Discovered {len(vehicle_urls)} vehicles to process")
        return vehicle_urls
    
    async def _process_vehicles(self, vehicle_urls, dealer_config):
        """
        Process each vehicle in the inventory.
        
        Args:
            vehicle_urls (list): List of vehicle URLs
            dealer_config (dict): Dealer configuration
        """
        logger.info(f"Processing {len(vehicle_urls)} vehicles")
        
        window_sticker_module = self.modules.get('window_sticker')
        feature_mapping_module = self.modules.get('feature_mapping')
        checkbox_module = self.modules.get('checkbox_management')
        
        if not all([window_sticker_module, feature_mapping_module, checkbox_module]):
            raise ValueError("Required modules not registered")
        
        # Load feature mapping configuration
        try:
            with open("configs/feature_mapping.json", "r") as f:
                feature_mapping = json.load(f)
        except Exception as e:
            logger.error(f"Error loading feature mapping: {str(e)}")
            raise
        
        # Apply dealer-specific overrides if available
        if 'feature_mapping_overrides' in dealer_config:
            for feature, mapping in dealer_config['feature_mapping_overrides'].items():
                feature_mapping[feature] = mapping
        
        # Process each vehicle
        for i, vehicle_url in enumerate(vehicle_urls):
            try:
                # Check if session is still valid, re-authenticate if needed
                if not await self.nova_engine.is_session_valid():
                    logger.info("Session expired, re-authenticating")
                    await self._authenticate(dealer_config)
                
                logger.info(f"Processing vehicle {i+1}/{len(vehicle_urls)}: {vehicle_url}")
                
                # Extract window sticker features
                features = await window_sticker_module.process_window_sticker(vehicle_url)
                self.processing_stats['features_found'] += len(features)
                
                # Map features to checkboxes
                feature_states = feature_mapping_module.map_features(
                    features, 
                    feature_mapping, 
                    self.config['feature_mapping']['confidence_threshold']
                )
                mapped_features = sum(1 for state in feature_states.values() if state)
                self.processing_stats['features_mapped'] += mapped_features
                
                # Update checkboxes
                results = await checkbox_module.update_checkboxes(vehicle_url, feature_states)
                self.processing_stats['checkboxes_updated'] += results['updated']
                
                # Update processing statistics
                self.processing_stats['vehicles_processed'] += 1
                if results['failed'] > 0:
                    self.processing_stats['failed_updates'] += 1
                else:
                    self.processing_stats['successful_updates'] += 1
                
                # Add short delay between vehicles to prevent rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing vehicle {vehicle_url}: {str(e)}")
                self.processing_stats['failed_updates'] += 1
        
        logger.info(f"Completed processing {len(vehicle_urls)} vehicles")
