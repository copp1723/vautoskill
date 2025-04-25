#!/usr/bin/env python3
"""
Test script for vAuto Feature Verification System workflow.

This script tests the basic workflow for a single dealership with mock data.
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.nova_engine import NovaActEngine
from src.modules.authentication.auth_module import AuthenticationModule
from src.modules.inventory.inventory_discovery import InventoryDiscoveryModule
from src.modules.inventory.window_sticker import WindowStickerModule
from src.modules.inventory.checkbox_management import CheckboxManagementModule
from src.modules.feature_mapping.feature_mapper import FeatureMappingModule
from src.modules.reporting.reporting import ReportingModule
from src.modules.workflow import WorkflowModule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Mock dealer configuration for testing
MOCK_DEALER_CONFIG = {
    "dealer_id": "test_dealer",
    "name": "Test Dealership",
    "timezone": "America/Chicago",
    "credentials": {
        "username": "test_user",
        "password": "test_password",
        "auth_email": "test@example.com"
    },
    "schedules": {
        "morning_run": "07:00",
        "afternoon_run": "14:00"
    },
    "report_recipients": ["test@example.com"]
}

# Mock system configuration for testing
MOCK_SYSTEM_CONFIG = {
    "nova_act": {
        "timeout": 10,
        "retry_attempts": 1,
        "headless": True
    },
    "feature_mapping": {
        "confidence_threshold": 90,
        "similarity_algorithm": "fuzzywuzzy.ratio"
    },
    "processing": {
        "max_vehicles_per_batch": 3,
        "session_timeout": 5
    },
    "reporting": {
        "email_recipients": ["test@example.com"],
        "log_level": "INFO",
        "store_logs_days": 7
    }
}

async def test_workflow():
    """
    Test the complete workflow with mock data.
    """
    logger.info("Starting workflow test...")
    
    # Initialize modules
    nova_engine = NovaActEngine(MOCK_SYSTEM_CONFIG)
    
    inventory_discovery = InventoryDiscoveryModule(nova_engine, MOCK_SYSTEM_CONFIG)
    window_sticker = WindowStickerModule(nova_engine, MOCK_SYSTEM_CONFIG)
    checkbox_management = CheckboxManagementModule(nova_engine, MOCK_SYSTEM_CONFIG)
    reporting = ReportingModule(MOCK_SYSTEM_CONFIG)
    
    # Create and configure workflow
    workflow = WorkflowModule(nova_engine, MOCK_SYSTEM_CONFIG)
    workflow.register_module('authentication', AuthenticationModule)
    workflow.register_module('inventory_discovery', inventory_discovery)
    workflow.register_module('window_sticker', window_sticker)
    workflow.register_module('feature_mapping', FeatureMappingModule)
    workflow.register_module('checkbox_management', checkbox_management)
    
    # Create mock feature mapping
    with open("configs/feature_mapping.json", "r") as f:
        feature_mapping = json.load(f)
    
    try:
        # Run workflow
        logger.info("Running workflow...")
        stats = await workflow.run_workflow(MOCK_DEALER_CONFIG)
        
        # Generate report
        logger.info("Generating report...")
        report_file = await reporting.generate_report(MOCK_DEALER_CONFIG, stats)
        
        # Log metrics
        logger.info("Logging metrics...")
        reporting.log_metrics(MOCK_DEALER_CONFIG, stats)
        
        # Display results
        logger.info("Test completed successfully")
        logger.info(f"Processed {stats['vehicles_processed']} vehicles")
        logger.info(f"Updated {stats['checkboxes_updated']} checkboxes")
        logger.info(f"Report generated: {report_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False
    finally:
        # Ensure browser is closed
        await nova_engine.close_browser()

def run_test():
    """
    Run the test asynchronously.
    """
    logger.info("Starting vAuto Feature Verification System test...")
    
    try:
        # Run the test asynchronously
        result = asyncio.run(test_workflow())
        
        if result:
            logger.info("Test passed")
            return 0
        else:
            logger.error("Test failed")
            return 1
            
    except Exception as e:
        logger.error(f"Test execution error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(run_test())
