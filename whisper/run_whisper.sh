#!/bin/bash

# Check if conda is available
if command -v conda &> /dev/null; then
    echo "Creating conda environment..."
    # Create conda environment if it doesn't exist
    conda env create -f environment.yml 2>/dev/null || conda env update -f environment.yml
    # Activate conda environment
    conda activate echoglobe_whisper
else
    echo "Creating Python virtual environment..."
    # Create virtual environment if it doesn't exist
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
fi

# Run the Whisper service
echo "Starting Whisper service..."
python main.py 