#!/bin/bash
# Timspeak Raspberry Pi Installation Script

set -e  # Exit on error

echo "============================================================"
echo "Timspeak Raspberry Pi - Installation Script"
echo "============================================================"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "WARNING: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "Project directory: $PROJECT_DIR"
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    echo "Install with: sudo apt-get install python3 python3-pip python3-venv"
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-venv \
    python3-pip \
    portaudio19-dev \
    libportaudio2 \
    python3-pyaudio \
    git

echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "Creating config.yaml from example..."
    cp config.yaml.example config.yaml
    echo ""
    echo "⚠️  IMPORTANT: Edit config.yaml and add your API keys!"
    echo "   nano config.yaml"
    echo ""
fi

# Setup USB HID
echo "============================================================"
echo "USB HID Keyboard Setup"
echo "============================================================"
echo ""
read -p "Configure USB HID keyboard emulation? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    bash setup/usb_hid_setup.sh
fi

echo ""

# Setup systemd service
echo "============================================================"
echo "Systemd Service Setup (Auto-start on boot)"
echo "============================================================"
echo ""
read -p "Install systemd service for auto-start? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing systemd service..."

    # Update service file with correct paths
    sed "s|/home/pi/Timspeak/RaspberryPi|$PROJECT_DIR|g" timspeak.service > /tmp/timspeak.service

    # Install service
    sudo cp /tmp/timspeak.service /etc/systemd/system/timspeak.service
    sudo systemctl daemon-reload
    sudo systemctl enable timspeak.service

    echo "✓ Systemd service installed"
    echo ""
    echo "Service commands:"
    echo "  sudo systemctl start timspeak   # Start service"
    echo "  sudo systemctl stop timspeak    # Stop service"
    echo "  sudo systemctl status timspeak  # Check status"
    echo "  sudo journalctl -u timspeak -f  # View logs"
    echo ""
fi

echo ""
echo "============================================================"
echo "Installation Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Edit config.yaml and add your API keys"
echo "2. Test: python3 main.py"
echo "3. If installed as service: sudo systemctl start timspeak"
echo ""
echo "Hardware wiring (BCM pin numbers):"
echo "  - Listen button: GPIO 17 → GND"
echo "  - Send button: GPIO 27 → GND"
echo "  - LED: GPIO 22 → 220Ω resistor → LED → GND"
echo ""
