#!/usr/bin/env python3
"""
Setup script for vAuto Feature Verification System.

This script:
1. Creates necessary directories
2. Verifies dependencies are installed
3. Checks for .env file and prompts for creation if missing
4. Verifies configuration files exist and are valid
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def create_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        "reports",
        "logs"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

def verify_dependencies():
    """Verify that all required dependencies are installed."""
    required_packages = [
        "nova_act",
        "fuzzywuzzy",
        "python-dotenv",
        "apscheduler"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print("\nMissing dependencies. Install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        install = input("Install missing dependencies now? (y/n): ")
        if install.lower() == 'y':
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("Dependencies installed successfully")

def check_env_file():
    """Check if .env file exists, create it if missing."""
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            print(".env file not found, but .env.example exists")
            create = input("Create .env file from example? (y/n): ")
            if create.lower() == 'y':
                with open(".env.example", "r") as example:
                    content = example.read()
                
                with open(".env", "w") as env_file:
                    env_file.write(content)
                
                print(".env file created. Please edit it with your API key and settings")
                return False
        else:
            print("Neither .env nor .env.example found. Creating basic .env file")
            with open(".env", "w") as env_file:
                env_file.write("# vAuto Feature Verification System Environment Variables\n")
                env_file.write("NOVA_ACT_API_KEY=your_api_key_here\n")
                env_file.write("LOG_LEVEL=INFO\n")
            
            print(".env file created. Please edit it with your API key")
            return False
    else:
        print("✅ .env file exists")
        return True

def verify_config_files():
    """Verify that all configuration files exist and are valid JSON."""
    config_files = [
        "configs/system_config.json",
        "configs/dealership_config.json",
        "configs/feature_mapping.json"
    ]
    
    all_valid = True
    for config_file in config_files:
        if not os.path.exists(config_file):
            print(f"❌ Configuration file missing: {config_file}")
            all_valid = False
            continue
        
        try:
            with open(config_file, "r") as f:
                json.load(f)
            print(f"✅ Configuration file valid: {config_file}")
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in configuration file: {config_file}")
            all_valid = False
    
    return all_valid

def main():
    """Main setup function."""
    print("Setting up vAuto Feature Verification System...\n")
    
    # Create necessary directories
    print("\n--- Creating Directories ---")
    create_directories()
    
    # Verify dependencies
    print("\n--- Verifying Dependencies ---")
    verify_dependencies()
    
    # Check for .env file
    print("\n--- Checking Environment Variables ---")
    env_valid = check_env_file()
    
    # Verify config files
    print("\n--- Verifying Configuration Files ---")
    config_valid = verify_config_files()
    
    # Final status
    print("\n--- Setup Summary ---")
    if env_valid and config_valid:
        print("✅ Setup complete. The system is ready to run.")
        print("To start the system, run: python src/main.py")
        print("To run a test, run: python src/main.py --test")
    else:
        print("⚠️ Setup incomplete. Please address the issues above before running the system.")

if __name__ == "__main__":
    main()
