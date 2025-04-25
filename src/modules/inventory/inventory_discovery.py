"""
Inventory Discovery Module for vAuto Feature Verification System.

Handles:
- Discovery of vehicles in the inventory
- Filtering of vehicles that need feature verification
- Retrieval of window sticker URLs
"""

import logging
import asyncio
import re
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

class InventoryDiscoveryModule:
    """
    Module for discovering vehicles in inventory that need feature verification.
    """
    
    def __init__(self, nova_engine, auth_module, config):
        """
        Initialize the inventory discovery module.
        
        Args:
            nova_engine (NovaActEngine): Nova Act Engine instance
            auth_module (AuthenticationModule): Authentication module instance
            config (dict): System configuration
        """
        self.nova_engine = nova_engine
        self.auth_module = auth_module
        self.config = config
        
        logger.info("Inventory Discovery module initialized")
    
    async def get_vehicles_needing_verification(self, dealership_config, max_vehicles=None):
        """
        Get vehicles that need feature verification.
        
        Args:
            dealership_config (dict): Dealership configuration
            max_vehicles (int, optional): Maximum number of vehicles to retrieve
            
        Returns:
            list: List of vehicle data dictionaries
        """
        if max_vehicles is None:
            max_vehicles = self.config["processing"]["max_vehicles_per_batch"]
        
        logger.info(f"Discovering vehicles needing verification for {dealership_config['name']} (max: {max_vehicles})")
        
        # Ensure logged in
        logged_in = await self.auth_module.ensure_logged_in(dealership_config.get("dealership_id"))
        if not logged_in:
            logger.error("Not logged in, cannot discover inventory")
            return []
        
        try:
            vehicles = await self.nova_engine.execute_action(
                lambda browser: self._discover_vehicles_action(browser, dealership_config, max_vehicles)
            )
            
            logger.info(f"Discovered {len(vehicles)} vehicles needing verification")
            return vehicles
            
        except Exception as e:
            logger.error(f"Error discovering vehicles: {str(e)}")
            return []
    
    async def _discover_vehicles_action(self, browser, dealership_config, max_vehicles):
        """
        Internal action to discover vehicles.
        
        Args:
            browser: Browser instance
            dealership_config (dict): Dealership configuration
            max_vehicles (int): Maximum number of vehicles to retrieve
            
        Returns:
            list: List of vehicle data dictionaries
        """
        vehicles = []
        
        try:
            # Navigate to inventory page
            await self._navigate_to_inventory(dealership_config)
            
            # Apply filters to find vehicles needing verification
            await self._apply_inventory_filters(dealership_config)
            
            # Extract vehicle data
            vehicles = await self._extract_vehicle_data(max_vehicles)
            
            return vehicles
            
        except Exception as e:
            logger.error(f"Discover vehicles action failed: {str(e)}")
            raise
    
    async def _navigate_to_inventory(self, dealership_config):
        """
        Navigate to the inventory page.
        
        Args:
            dealership_config (dict): Dealership configuration
        """
        logger.info("Navigating to inventory page")
        
        # Go to inventory section
        await self.nova_engine.navigate_to("https://www.vauto.com/inventory")
        
        # Wait for inventory to load
        inventory_loaded = await self.nova_engine.wait_for_presence(
            By.XPATH, 
            "//div[contains(@class, 'inventory-grid') or contains(@class, 'inventory-table')]"
        )
        
        if not inventory_loaded:
            logger.error("Inventory page failed to load")
            raise Exception("Inventory page failed to load")
        
        logger.info("Successfully navigated to inventory page")
    
    async def _apply_inventory_filters(self, dealership_config):
        """
        Apply filters to find vehicles needing verification.
        
        Args:
            dealership_config (dict): Dealership configuration
        """
        logger.info("Applying inventory filters")
        
        try:
            # Look for filter/search button
            filter_buttons = [
                "//button[contains(text(), 'Filter')]",
                "//button[contains(@class, 'filter')]",
                "//button[contains(text(), 'Search')]",
                "//button[contains(@class, 'search')]"
            ]
            
            filter_button = None
            for selector in filter_buttons:
                try:
                    elements = await self.nova_engine.find_elements(By.XPATH, selector)
                    if elements:
                        filter_button = elements[0]
                        break
                except:
                    continue
            
            if filter_button:
                await self.nova_engine.click_element(filter_button)
                
                # Wait for filter panel to appear
                await asyncio.sleep(1)
                
                # Apply specific filters from dealership config
                if "inventory_filters" in dealership_config:
                    for filter_name, filter_value in dealership_config["inventory_filters"].items():
                        await self._apply_specific_filter(filter_name, filter_value)
                
                # If no specific filters, use default: only new vehicles
                else:
                    await self._apply_specific_filter("status", "New")
                
                # Apply the filters by clicking apply/search button
                apply_buttons = [
                    "//button[contains(text(), 'Apply')]",
                    "//button[contains(text(), 'Search')]",
                    "//button[contains(@class, 'apply')]",
                    "//button[contains(@class, 'search-button')]"
                ]
                
                for selector in apply_buttons:
                    try:
                        apply_button = await self.nova_engine.find_element(By.XPATH, selector)
                        if apply_button:
                            await self.nova_engine.click_element(apply_button)
                            
                            # Wait for results to load
                            await asyncio.sleep(2)
                            break
                    except:
                        continue
            
            # Wait for filtered results to load
            await self.nova_engine.wait_for_invisibility(
                By.XPATH, 
                "//div[contains(@class, 'loading') or contains(@class, 'spinner')]"
            )
            
            logger.info("Inventory filters applied")
            
        except Exception as e:
            logger.error(f"Error applying inventory filters: {str(e)}")
            # Continue without filters if they fail
            logger.warning("Continuing without filters")
    
    async def _apply_specific_filter(self, filter_name, filter_value):
        """
        Apply a specific filter.
        
        Args:
            filter_name (str): Filter name
            filter_value (str): Filter value
        """
        logger.debug(f"Applying filter: {filter_name} = {filter_value}")
        
        try:
            # Find filter field
            filter_selectors = [
                f"//label[contains(text(), '{filter_name}')]/following-sibling::input",
                f"//div[contains(text(), '{filter_name}')]/following-sibling::input",
                f"//input[@name='{filter_name}']",
                f"//select[@name='{filter_name}']",
                f"//div[contains(@class, '{filter_name.lower()}')]//input"
            ]
            
            filter_field = None
            for selector in filter_selectors:
                try:
                    elements = await self.nova_engine.find_elements(By.XPATH, selector)
                    if elements:
                        filter_field = elements[0]
                        break
                except:
                    continue
            
            if not filter_field:
                logger.warning(f"Filter field not found: {filter_name}")
                return
            
            # Check field type (input, select, checkbox, etc.)
            field_type = await self.nova_engine.get_attribute(filter_field, "type")
            
            if field_type == "checkbox":
                # Handle checkbox
                current_state = await self.nova_engine.get_attribute(filter_field, "checked")
                if (current_state and filter_value.lower() in ("false", "no", "0")) or \
                   (not current_state and filter_value.lower() in ("true", "yes", "1")):
                    await self.nova_engine.click_element(filter_field)
            
            elif field_type in ("text", "search", "number"):
                # Handle text input
                await self.nova_engine.fill_input(filter_field, filter_value)
            
            else:
                # Try to find dropdown option
                await self.nova_engine.click_element(filter_field)  # Open dropdown
                
                await asyncio.sleep(1)  # Wait for dropdown options to appear
                
                # Look for matching option
                option_selectors = [
                    f"//option[contains(text(), '{filter_value}')]",
                    f"//div[contains(text(), '{filter_value}')]",
                    f"//li[contains(text(), '{filter_value}')]"
                ]
                
                for selector in option_selectors:
                    try:
                        option = await self.nova_engine.find_element(By.XPATH, selector)
                        if option:
                            await self.nova_engine.click_element(option)
                            break
                    except:
                        continue
        
        except Exception as e:
            logger.warning(f"Error applying filter {filter_name}: {str(e)}")
    
    async def _extract_vehicle_data(self, max_vehicles):
        """
        Extract vehicle data from the inventory page.
        
        Args:
            max_vehicles (int): Maximum number of vehicles to retrieve
            
        Returns:
            list: List of vehicle data dictionaries
        """
        logger.info(f"Extracting vehicle data (max: {max_vehicles})")
        
        vehicles = []
        
        try:
            # Identify vehicle elements
            vehicle_rows = await self.nova_engine.find_elements(
                By.XPATH,
                "//div[contains(@class, 'inventory-row') or contains(@class, 'vehicle-row') or contains(@class, 'inventory-item')]"
            )
            
            if not vehicle_rows:
                logger.warning("No vehicle rows found, trying alternative selectors")
                
                # Try alternate selectors
                vehicle_rows = await self.nova_engine.find_elements(
                    By.XPATH,
                    "//tr[contains(@class, 'inventory') or contains(@data-vehicle-id, '') or .//a[contains(@href, 'vehicle')]]"
                )
            
            if not vehicle_rows:
                logger.error("No vehicles found in inventory")
                return []
            
            # Limit to max_vehicles
            vehicle_rows = vehicle_rows[:max_vehicles]
            
            logger.info(f"Found {len(vehicle_rows)} vehicle rows")
            
            # Process each vehicle row
            for row in vehicle_rows:
                try:
                    # Extract vehicle ID
                    vehicle_id = await self.nova_engine.get_attribute(row, "data-vehicle-id")
                    
                    if not vehicle_id:
                        # Try to extract from other attributes
                        vehicle_id = await self._extract_vehicle_id_from_element(row)
                    
                    if not vehicle_id:
                        logger.warning("Could not extract vehicle ID, skipping")
                        continue
                    
                    # Extract vehicle detail URL
                    detail_url = await self._extract_detail_url(row)
                    
                    # Extract basic vehicle info
                    vehicle_info = await self._extract_vehicle_info(row)
                    
                    # Create vehicle data entry
                    vehicle_data = {
                        "id": vehicle_id,
                        "detail_url": detail_url,
                        **vehicle_info
                    }
                    
                    vehicles.append(vehicle_data)
                    
                except Exception as e:
                    logger.warning(f"Error extracting data for vehicle row: {str(e)}")
                    continue
            
            logger.info(f"Extracted data for {len(vehicles)} vehicles")
            
            # For each vehicle, get window sticker URL
            vehicles_with_stickers = []
            
            for vehicle in vehicles:
                try:
                    if "detail_url" in vehicle and vehicle["detail_url"]:
                        window_sticker_url = await self._get_window_sticker_url(vehicle["detail_url"])
                        if window_sticker_url:
                            vehicle["window_sticker_url"] = window_sticker_url
                            vehicles_with_stickers.append(vehicle)
                except Exception as e:
                    logger.warning(f"Error getting window sticker URL for vehicle {vehicle.get('id')}: {str(e)}")
            
            logger.info(f"Found window sticker URLs for {len(vehicles_with_stickers)} vehicles")
            return vehicles_with_stickers
            
        except Exception as e:
            logger.error(f"Error extracting vehicle data: {str(e)}")
            return []
    
    async def _extract_vehicle_id_from_element(self, element):
        """
        Extract vehicle ID from element.
        
        Args:
            element: Vehicle row element
            
        Returns:
            str: Vehicle ID or None if not found
        """
        # Try various attributes that might contain the ID
        attrs_to_check = ["id", "data-id", "data-key", "data-row-key"]
        
        for attr in attrs_to_check:
            value = await self.nova_engine.get_attribute(element, attr)
            if value:
                # Extract numeric ID if present
                match = re.search(r'\d+', value)
                if match:
                    return match.group(0)
                return value
        
        # Try to find links that might contain the ID
        links = await self.nova_engine.find_elements(
            By.XPATH,
            ".//a[contains(@href, 'vehicle') or contains(@href, 'inventory') or contains(@href, 'detail')]",
            element
        )
        
        for link in links:
            href = await self.nova_engine.get_attribute(link, "href")
            if href:
                # Extract ID from URL
                match = re.search(r'[?&]id=(\d+)', href)
                if match:
                    return match.group(1)
        
        return None
    
    async def _extract_detail_url(self, row):
        """
        Extract vehicle detail URL from row.
        
        Args:
            row: Vehicle row element
            
        Returns:
            str: Detail URL or None if not found
        """
        # Look for links
        links = await self.nova_engine.find_elements(
            By.XPATH,
            ".//a[contains(@href, 'vehicle') or contains(@href, 'inventory') or contains(@href, 'detail')]",
            row
        )
        
        for link in links:
            href = await self.nova_engine.get_attribute(link, "href")
            if href:
                return href
        
        # If no links found, try to construct URL from vehicle ID
        vehicle_id = await self.nova_engine.get_attribute(row, "data-vehicle-id")
        if vehicle_id:
            return f"https://www.vauto.com/inventory/vehicle/{vehicle_id}"
        
        return None
    
    async def _extract_vehicle_info(self, row):
        """
        Extract basic vehicle info from row.
        
        Args:
            row: Vehicle row element
            
        Returns:
            dict: Vehicle information
        """
        info = {
            "make": None,
            "model": None,
            "year": None,
            "vin": None,
            "stock_number": None
        }
        
        # Try to extract VIN
        vin_elements = await self.nova_engine.find_elements(
            By.XPATH,
            ".//div[contains(text(), 'VIN:') or contains(text(), 'VIN')]",
            row
        )
        
        for element in vin_elements:
            text = await self.nova_engine.get_text(element)
            match = re.search(r'VIN:?\s*([A-Z0-9]{17})', text)
            if match:
                info["vin"] = match.group(1)
                break
        
        # Extract stock number
        stock_elements = await self.nova_engine.find_elements(
            By.XPATH,
            ".//div[contains(text(), 'Stock:') or contains(text(), 'Stock')]",
            row
        )
        
        for element in stock_elements:
            text = await self.nova_engine.get_text(element)
            match = re.search(r'Stock:?\s*([A-Z0-9]+)', text)
            if match:
                info["stock_number"] = match.group(1)
                break
        
        # Try to extract year/make/model from text
        make_model_elements = await self.nova_engine.find_elements(
            By.XPATH,
            ".//div[contains(@class, 'make') or contains(@class, 'model') or contains(@class, 'vehicle-name')]",
            row
        )
        
        for element in make_model_elements:
            text = await self.nova_engine.get_text(element)
            if text:
                # Try to extract year (4 digits)
                year_match = re.search(r'(20\d{2})', text)
                if year_match:
                    info["year"] = year_match.group(1)
                
                # Common makes
                makes = [
                    "Ford", "Chevrolet", "Chevy", "Toyota", "Honda", "Nissan", "Hyundai", 
                    "Kia", "BMW", "Mercedes", "Audi", "Lexus", "Acura", "Mazda", "Subaru",
                    "Jeep", "Dodge", "Chrysler", "Ram", "GMC", "Buick", "Cadillac", "Lincoln",
                    "Infiniti", "Volkswagen", "VW", "Volvo", "Porsche", "Land Rover", "Jaguar",
                    "Mitsubishi", "Genesis", "Tesla"
                ]
                
                for make in makes:
                    if re.search(r'\b' + re.escape(make) + r'\b', text, re.IGNORECASE):
                        info["make"] = make
                        
                        # Try to extract model after make
                        model_pattern = r'\b' + re.escape(make) + r'\s+([A-Za-z0-9\-]+)'
                        model_match = re.search(model_pattern, text, re.IGNORECASE)
                        if model_match:
                            info["model"] = model_match.group(1)
                        break
        
        return info
    
    async def _get_window_sticker_url(self, detail_url):
        """
        Get window sticker URL for a vehicle.
        
        Args:
            detail_url (str): Vehicle detail URL
            
        Returns:
            str: Window sticker URL or None if not found
        """
        logger.info(f"Getting window sticker URL for vehicle: {detail_url}")
        
        try:
            # Navigate to vehicle detail page
            await self.nova_engine.navigate_to(detail_url)
            
            # Wait for detail page to load
            await self.nova_engine.wait_for_presence(
                By.XPATH,
                "//div[contains(@class, 'vehicle-detail') or contains(@class, 'inventory-detail')]"
            )
            
            # Look for window sticker link or button
            window_sticker_selectors = [
                "//a[contains(text(), 'Window Sticker') or contains(@aria-label, 'Window Sticker')]",
                "//button[contains(text(), 'Window Sticker')]",
                "//div[contains(text(), 'Window Sticker')]/parent::a",
                "//a[contains(@href, 'window-sticker') or contains(@href, 'sticker.pdf')]"
            ]
            
            for selector in window_sticker_selectors:
                try:
                    elements = await self.nova_engine.find_elements(By.XPATH, selector)
                    for element in elements:
                        href = await self.nova_engine.get_attribute(element, "href")
                        if href and ('pdf' in href.lower() or 'sticker' in href.lower() or 'window' in href.lower()):
                            logger.info(f"Found window sticker URL: {href}")
                            return href
                except:
                    continue
            
            # Try to navigate to Equipment tab if available
            equipment_tab_selectors = [
                "//a[contains(text(), 'Equipment') or contains(@aria-label, 'Equipment')]",
                "//div[contains(text(), 'Equipment')]/parent::a",
                "//button[contains(text(), 'Equipment')]"
            ]
            
            for selector in equipment_tab_selectors:
                try:
                    element = await self.nova_engine.find_element(By.XPATH, selector, timeout=3)
                    if element:
                        await self.nova_engine.click_element(element)
                        
                        # Wait for tab to load
                        await asyncio.sleep(1)
                        
                        # Look for window sticker on this tab
                        for selector in window_sticker_selectors:
                            try:
                                elements = await self.nova_engine.find_elements(By.XPATH, selector)
                                for element in elements:
                                    href = await self.nova_engine.get_attribute(element, "href")
                                    if href and ('pdf' in href.lower() or 'sticker' in href.lower() or 'window' in href.lower()):
                                        logger.info(f"Found window sticker URL: {href}")
                                        return href
                            except:
                                continue
                        
                        break
                except:
                    continue
            
            logger.warning(f"No window sticker URL found for vehicle: {detail_url}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting window sticker URL: {str(e)}")
            return None
