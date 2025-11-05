#!/bin/bash
# USB HID Gadget Mode Setup for Raspberry Pi
# Configures the Pi to act as a USB keyboard

set -e

echo "============================================================"
echo "USB HID Keyboard Gadget Mode Setup"
echo "============================================================"
echo ""

# Check if running on Raspberry Pi 4 or Zero
if [ ! -f /proc/device-tree/model ]; then
    echo "ERROR: Cannot detect Raspberry Pi model"
    exit 1
fi

MODEL=$(cat /proc/device-tree/model)
echo "Detected: $MODEL"
echo ""

if [[ ! $MODEL =~ "Raspberry Pi 4" ]] && [[ ! $MODEL =~ "Raspberry Pi Zero" ]]; then
    echo "WARNING: USB gadget mode is designed for Pi 4 or Pi Zero"
    echo "Other models may not support USB OTG"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Enable dwc2 overlay in /boot/config.txt
echo "Configuring /boot/config.txt..."

if ! grep -q "dtoverlay=dwc2" /boot/config.txt; then
    echo "dtoverlay=dwc2" | sudo tee -a /boot/config.txt
    echo "✓ Added dtoverlay=dwc2"
else
    echo "✓ dtoverlay=dwc2 already present"
fi

# Enable dwc2 and libcomposite modules
echo "Configuring /etc/modules..."

if ! grep -q "dwc2" /etc/modules; then
    echo "dwc2" | sudo tee -a /etc/modules
    echo "✓ Added dwc2 module"
else
    echo "✓ dwc2 module already present"
fi

if ! grep -q "libcomposite" /etc/modules; then
    echo "libcomposite" | sudo tee -a /etc/modules
    echo "✓ Added libcomposite module"
else
    echo "✓ libcomposite module already present"
fi

# Create USB gadget configuration script
echo "Creating USB HID configuration script..."

sudo tee /usr/local/bin/timspeak-usb-gadget.sh > /dev/null <<'EOF'
#!/bin/bash
# USB HID Keyboard Gadget Configuration

# Load modules
modprobe libcomposite
cd /sys/kernel/config/usb_gadget/

# Create gadget
mkdir -p timspeak
cd timspeak

# USB IDs
echo 0x1d6b > idVendor  # Linux Foundation
echo 0x0104 > idProduct # Multifunction Composite Gadget
echo 0x0100 > bcdDevice # v1.0.0
echo 0x0200 > bcdUSB    # USB 2.0

# Device info
mkdir -p strings/0x409
echo "fedcba9876543210" > strings/0x409/serialnumber
echo "Timspeak" > strings/0x409/manufacturer
echo "Timspeak Dictation Device" > strings/0x409/product

# Configuration
mkdir -p configs/c.1/strings/0x409
echo "Config 1: HID Keyboard" > configs/c.1/strings/0x409/configuration
echo 250 > configs/c.1/MaxPower

# HID Keyboard Function
mkdir -p functions/hid.usb0
echo 1 > functions/hid.usb0/protocol  # Keyboard
echo 1 > functions/hid.usb0/subclass  # Boot interface subclass
echo 8 > functions/hid.usb0/report_length

# HID Report Descriptor (standard keyboard)
echo -ne \\x05\\x01\\x09\\x06\\xa1\\x01\\x05\\x07\\x19\\xe0\\x29\\xe7\\x15\\x00\\x25\\x01\\x75\\x01\\x95\\x08\\x81\\x02\\x95\\x01\\x75\\x08\\x81\\x03\\x95\\x05\\x75\\x01\\x05\\x08\\x19\\x01\\x29\\x05\\x91\\x02\\x95\\x01\\x75\\x03\\x91\\x03\\x95\\x06\\x75\\x08\\x15\\x00\\x25\\x65\\x05\\x07\\x19\\x00\\x29\\x65\\x81\\x00\\xc0 > functions/hid.usb0/report_desc

# Link function to configuration
ln -s functions/hid.usb0 configs/c.1/

# Enable gadget
ls /sys/class/udc > UDC

# Set permissions for HID device
sleep 1
chmod 666 /dev/hidg0

echo "USB HID Keyboard gadget configured"
EOF

sudo chmod +x /usr/local/bin/timspeak-usb-gadget.sh
echo "✓ Created /usr/local/bin/timspeak-usb-gadget.sh"

# Create systemd service to run gadget script on boot
echo "Creating systemd service for USB gadget..."

sudo tee /etc/systemd/system/timspeak-usb-gadget.service > /dev/null <<'EOF'
[Unit]
Description=Timspeak USB HID Keyboard Gadget
After=network.target
DefaultDependencies=no
Before=sysinit.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/timspeak-usb-gadget.sh

[Install]
WantedBy=sysinit.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable timspeak-usb-gadget.service
echo "✓ USB gadget service enabled"

echo ""
echo "============================================================"
echo "USB HID Setup Complete!"
echo "============================================================"
echo ""
echo "⚠️  IMPORTANT: You must REBOOT for changes to take effect"
echo ""
echo "After reboot:"
echo "  1. Connect Pi to computer via USB data port"
echo "  2. Pi will appear as a USB keyboard"
echo "  3. Test with: echo 'test' | sudo tee /dev/hidg0"
echo ""
read -p "Reboot now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo reboot
fi
