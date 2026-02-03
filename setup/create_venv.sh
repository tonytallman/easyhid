#!/bin/bash
# Create EasyHID venv and install Python dependencies (avoids externally-managed-environment).
# Requires system D-Bus/GObject packages (run setup/install.sh first, or):
#   sudo apt install -y python3-dbus python3-gi python3-evdev python3.12-venv

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"

cd "$PROJECT_ROOT"

if ! python3 -c "import venv" 2>/dev/null; then
    echo "Error: python3-venv is not installed. Install it with:"
    echo "  sudo apt install -y python3.12-venv   # or python3-venv"
    exit 1
fi

# D-Bus and PyGObject from pip often fail to build; we use system packages via --system-site-packages
for mod in dbus gi; do
    if ! python3 -c "import $mod" 2>/dev/null; then
        echo "Error: Python module '$mod' not found. Install system packages first:"
        echo "  sudo apt install -y python3-dbus python3-gi python3-evdev"
        echo "Then run this script again."
        exit 1
    fi
done

# Recreate venv so system-site-packages is enabled (needed for dbus/gi)
if [ -d "$VENV_DIR" ]; then
    echo "Removing existing .venv to enable system-site-packages ..."
    rm -rf "$VENV_DIR"
fi
echo "Creating virtual environment at $VENV_DIR (with system-site-packages for D-Bus/GI) ..."
python3 -m venv "$VENV_DIR" --system-site-packages

echo "Installing pip dependencies into the venv ..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r requirements.txt

echo ""
echo "Done. To run the app:"
echo "  source .venv/bin/activate"
echo "  python main.py"
echo ""
echo "Or without activating:"
echo "  .venv/bin/python main.py"
echo ""
