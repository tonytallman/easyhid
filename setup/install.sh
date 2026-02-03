#!/bin/bash
# Installation script for EasyHID

set -e

echo "EasyHID - Installation Script"
echo "=============================="
echo ""

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    echo "Error: Cannot detect Linux distribution"
    exit 1
fi

echo "Detected distribution: $DISTRO"
echo ""

# Install system dependencies based on distribution
echo "Installing system dependencies..."

case $DISTRO in
    ubuntu|debian)
        sudo apt update
        sudo apt install -y \
            python3 \
            python3-tk \
            python3-pip \
            python3-venv \
            python3-dbus \
            python3-gi \
            python3-evdev \
            bluetooth \
            bluez \
            dbus
        ;;
    fedora|rhel|centos)
        sudo dnf install -y \
            python3 \
            python3-tkinter \
            python3-pip \
            python3-dbus \
            python3-gobject \
            python3-evdev \
            bluez \
            dbus
        ;;
    arch|manjaro)
        sudo pacman -S --noconfirm \
            python \
            python-tkinter \
            python-pip \
            python-dbus \
            python-gobject \
            python-evdev \
            bluez \
            dbus
        ;;
    *)
        echo "Warning: Unsupported distribution. Please install dependencies manually:"
        echo "  - Python 3.10+"
        echo "  - python3-tk / python3-tkinter"
        echo "  - python3-dbus"
        echo "  - python3-gi / python3-gobject"
        echo "  - python3-evdev"
        echo "  - bluez"
        echo "  - dbus"
        exit 1
        ;;
esac

echo ""
echo "System dependencies installed."
echo ""

# Add user to input group
echo "Adding user to 'input' group for device access..."
CURRENT_USER=${SUDO_USER:-$USER}
if [ -z "$CURRENT_USER" ]; then
    CURRENT_USER=$(whoami)
fi

if groups "$CURRENT_USER" | grep -q "\binput\b"; then
    echo "User $CURRENT_USER is already in the 'input' group."
else
    sudo usermod -aG input "$CURRENT_USER"
    echo "User $CURRENT_USER added to 'input' group."
    echo ""
    echo "IMPORTANT: You must log out and log back in for group membership to take effect!"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Log out and log back in (to apply group membership)"
echo "2. Install Python dependencies: pip install -r requirements.txt"
echo "3. Run the application: python3 main.py"
echo ""
