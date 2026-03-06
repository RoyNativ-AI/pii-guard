#!/bin/bash

echo "Setting up Privacy Protector..."

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install the package in editable mode
pip install -e .

echo "Setup complete. Activate the virtual environment with 'source venv/bin/activate'"