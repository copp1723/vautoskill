#!/usr/bin/env python3
"""
vAuto Feature Verification System main entry point.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Add src directory to path to allow importing from modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.nova_engine import NovaActEngine
from src.modules.authentication.auth_module import AuthenticationModule
from src.modules.inventory.inventory_discovery import InventoryDiscoveryModule
from src.modules.inventory.window_sticker import WindowStickerModule
from src.modules.inventory.checkbox_management import CheckboxManagementModule
from src.modules.feature_mapping.feature_mapper import FeatureMappingModule
from src.modules.reporting.reporting import ReportingModule
from src.modules.workflow import WorkflowModule

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("vauto_verification.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def init_modules(system_config):
    """
    Initialize all system modules.
    
    Args:
        system_config (dict): System configuration
        
    Returns:
        dict: Initialized modules
    """
    # Initialize Nova Act Engine
    nova_engine = NovaActEngine(system_config)
    
    # Initialize modules
    inventory_discovery = InventoryDiscoveryModule(nova_engine, system_config)
    window_sticker = WindowStickerModule(nova_engine, system_config)
    checkbox_management = CheckboxManagementModule(nova_engine, system_config)
    reporting = ReportingModule(system_config)
    
    # Create workflow
    workflow = WorkflowModule(nova_engine, system_config)
    
    # Register modules with workflow
    workflow.register_module('authentication', AuthenticationModule)
    workflow.register_module('inventory_discovery', inventory_discovery)
    workflow.register_module('window_sticker', window_sticker)
    workflow.register_module('feature_mapping', FeatureMappingModule)
    workflow.register_module('checkbox_management', checkbox_management)
    
    return {
        'nova_engine': nova_engine,
        'inventory_discovery': inventory_discovery,
        'window_sticker': window_sticker,
        'checkbox_management': checkbox_management,
        'feature_mapping': FeatureMappingModule,
        'reporting': reporting,
        'workflow': workflow
    }

async def schedule_dealership(scheduler, workflow, reporting, dealer_config, system_config):
    """
    Schedule workflow execution for a dealership.
    
    Args:
        scheduler (AsyncIOScheduler): Scheduler instance
        workflow (WorkflowModule): Workflow module
        reporting (ReportingModule): Reporting module
        dealer_config (dict): Dealer configuration
        system_config (dict): System configuration
    """
    dealer_name = dealer_config['name']
    logger.info(f"Scheduling workflow for dealership: {dealer_name}")
    
    # Define the job function
    async def run_dealership_job():
        logger.info(f"Executing scheduled job for dealership: {dealer_name}")
        try:
            # Run workflow
            stats = await workflow.run_workflow(dealer_config)
            
            # Generate report
            report_file = await reporting.generate_report(dealer_config, stats)
            
            # Send notification
            await reporting.send_notification(dealer_config, stats, report_file)
            
            # Log metrics
            reporting.log_metrics(dealer_config, stats)
            
        except Exception as e:
            logger.error(f"Scheduled job failed for dealership {dealer_name}: {str(e)}")
    
    # Schedule morning run
    if 'morning_run' in dealer_config.get('schedules', {}):
        morning_time = dealer_config['schedules']['morning_run']
        hour, minute = map(int, morning_time.split(':'))
        
        scheduler.add_job(
            run_dealership_job,
            CronTrigger(hour=hour, minute=minute),
            id=f"{dealer_config['dealer_id']}_morning",
            replace_existing=True,
            name=f"{dealer_name} Morning Run"
        )
        logger.info(f"Scheduled morning run for {dealer_name} at {morning_time}")
    
    # Schedule afternoon run
    if 'afternoon_run' in dealer_config.get('schedules', {}):
        afternoon_time = dealer_config['schedules']['afternoon_run']
        hour, minute = map(int, afternoon_time.split(':'))
        
        scheduler.add_job(
            run_dealership_job,
            CronTrigger(hour=hour, minute=minute),
            id=f"{dealer_config['dealer_id']}_afternoon",
            replace_existing=True,
            name=f"{dealer_name} Afternoon Run"
        )
        logger.info(f"Scheduled afternoon run for {dealer_name} at {afternoon_time}")

async def main():
    """
    Main entry point for the vAuto Feature Verification System.
    """
    logger.info("Starting vAuto Feature Verification System...")
    
    # Load configuration
    try:
        with open("configs/system_config.json", "r") as f:
            system_config = json.load(f)
            
        with open("configs/dealership_config.json", "r") as f:
            dealership_config = json.load(f)
            
        with open("configs/feature_mapping.json", "r") as f:
            feature_mapping = json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return
    
    logger.info(f"Loaded configuration for {len(dealership_config)} dealerships")
    
    # Initialize modules
    modules = await init_modules(system_config)
    
    # Create scheduler
    scheduler = AsyncIOScheduler()
    
    # Schedule workflows for each dealership
    for dealer in dealership_config:
        await schedule_dealership(
            scheduler, 
            modules['workflow'], 
            modules['reporting'], 
            dealer, 
            system_config
        )
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started")
    
    # Run an immediate test execution if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--test" and len(dealership_config) > 0:
        logger.info("Running test execution for first dealership")
        test_dealer = dealership_config[0]
        try:
            # Run workflow
            stats = await modules['workflow'].run_workflow(test_dealer)
            
            # Generate report
            report_file = await modules['reporting'].generate_report(test_dealer, stats)
            
            # Send notification
            await modules['reporting'].send_notification(test_dealer, stats, report_file)
            
            # Log metrics
            modules['reporting'].log_metrics(test_dealer, stats)
            
            logger.info("Test execution completed successfully")
        except Exception as e:
            logger.error(f"Test execution failed: {str(e)}")
    
    logger.info("System initialization complete")
    # Keep the program running for scheduled tasks
    try:
        # Wait for keyboard interrupt
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("System shutdown initiated by user")
        scheduler.shutdown()
    
    logger.info("vAuto Feature Verification System shutting down")

if __name__ == "__main__":
    asyncio.run(main())
