#!/bin/bash

# Change to the project directory
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Run the program with test flag
echo "Running vAuto Feature Verification System..."
python src/main.py --test

# Deactivate virtual environment
deactivate
