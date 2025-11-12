#!/bin/bash

# EPWgen Installation Script
# This script creates a conda environment and installs EPWgen

set -e  # Exit on error

echo "=========================================="
echo "EPWgen Installation Script"
echo "=========================================="
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null
then
    echo "ERROR: conda is not installed or not in PATH"
    echo "Please install Anaconda or Miniconda first:"
    echo "https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Create environment
echo "Creating conda environment 'epwgen' with Python 3.11..."
conda create -n epwgen python=3.11 -y

# Activate environment
echo ""
echo "Activating environment..."
eval "$(conda shell.bash hook)"
conda activate epwgen

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Install EPWgen
echo ""
echo "Installing EPWgen..."
pip install -e .

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "To run EPWgen:"
echo "  1. Activate the environment: conda activate epwgen"
echo "  2. Run the application: epwgen"
echo ""
echo "Or use this one-liner:"
echo "  conda run -n epwgen epwgen"
echo ""
