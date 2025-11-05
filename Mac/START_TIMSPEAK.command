#!/bin/bash
# Timspeak Mac Launcher
# Double-click this file to start Timspeak

echo "============================================================"
echo "Timspeak - AI-Powered Dictation System (macOS)"
echo "============================================================"
echo ""

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org/"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Python detected:"
python3 --version
echo ""

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "WARNING: config.yaml not found"
    echo "Creating from config.yaml.example..."
    cp config.yaml.example config.yaml
    echo ""
    echo "IMPORTANT: Edit config.yaml and add your API keys before using Timspeak!"
    echo ""
    echo "Opening config.yaml in TextEdit..."
    open -e config.yaml
    echo ""
    read -p "Press Enter after you have configured your API keys..."
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Checking dependencies..."
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "WARNING: Some dependencies failed to install"
    echo "You may need to install them manually"
    echo ""
fi

echo ""
echo "============================================================"
echo "Starting Timspeak..."
echo "============================================================"
echo ""

# Start the application
python main.py

# If the application exits, wait before closing
echo ""
echo "Timspeak has stopped."
read -p "Press Enter to exit..."
