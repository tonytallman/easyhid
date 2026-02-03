# EasyHID

Bluetooth HID keyboard and mouse sharing for Linux.

A Linux application that exposes your keyboard and mouse (trackpad) as a Bluetooth HID device, allowing you to share input with other devices like Macs, Windows PCs, or Android devices.

## Features

- Share keyboard and mouse input over Bluetooth
- Exclusive input capture (input doesn't affect host system while sharing)
- Simple GUI with one-click sharing
- Emergency stop: Press Left Shift + Space + Right Shift simultaneously to stop sharing

## Requirements

- Linux system with Bluetooth support
- Python 3.10 or higher
- BlueZ 5.50+ (usually pre-installed)
- Root access or membership in the `input` group

## Installation

### 1. Install System Dependencies

Run the setup script:

```bash
chmod +x setup/install.sh
sudo ./setup/install.sh
```

Or manually:

```bash
# Ubuntu/Debian
sudo apt install python3-tk python3-dbus python3-gi bluetooth bluez python3-evdev

# Fedora
sudo dnf install python3-tkinter python3-dbus python3-gobject bluetooth bluez python3-evdev

# Arch Linux
sudo pacman -S python-tkinter python-dbus python-gobject bluez python-evdev
```

### 2. Add User to Input Group

```bash
sudo usermod -aG input $USER
```

**Important:** You must log out and log back in for the group membership to take effect.

### 3. Install Python Dependencies (use a virtual environment)

On Debian/Ubuntu, the system Python is externally managed and `dbus-python` often fails to build from pip. Use system packages for D-Bus/GObject and a venv with `--system-site-packages`:

```bash
# One-time: venv support + Python libs (D-Bus, GObject, evdev)
sudo apt install -y python3.12-venv python3-dbus python3-gi python3-evdev

# Create venv and install remaining deps (evdev from pip)
chmod +x setup/create_venv.sh
./setup/create_venv.sh

# Run the app
.venv/bin/python main.py
# Or: source .venv/bin/activate && python main.py
```

## Usage

### Starting the Application

```bash
python3 main.py
```

### Using the Application

1. Click the **"Share"** button to start sharing
2. The application will:
   - Make your device discoverable via Bluetooth
   - Start capturing keyboard and mouse input
   - Forward all input to connected Bluetooth devices
3. While sharing, your keyboard and mouse will have no effect on the Linux host system
4. To stop sharing:
   - Click the **"Stop"** button in the GUI, OR
   - Simultaneously press and hold **Left Shift + Space + Right Shift**

### Pairing with Another Device

1. Start sharing from the application
2. On your target device (Mac, Windows, Android, etc.), go to Bluetooth settings
3. Look for a device named "EasyHID"
4. Pair with the device
5. Once paired, keyboard and mouse input will be forwarded to that device

## Troubleshooting

### Permission Denied Errors

If you see permission errors accessing `/dev/input/event*`:

```bash
# Check if you're in the input group
groups | grep input

# If not, add yourself and log out/in
sudo usermod -aG input $USER
```

### Bluetooth HID already registered (UUID already registered)

If you see **"HID profile in use"** or **"UUID already registered"**, BlueZ’s built-in input plugin has already taken the HID profile. This app needs to own that profile, so the input plugin must be disabled while using the app.

**Option A – systemd override (persistent, recommended)**

```bash
sudo mkdir -p /etc/systemd/system/bluetooth.service.d
sudo tee /etc/systemd/system/bluetooth.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=/usr/libexec/bluetooth/bluetoothd --noplugin=input
EOF
```

If your system uses a different path for `bluetoothd`, find it with:

```bash
systemctl cat bluetooth | grep ExecStart
```

Use that path in the override, adding `--noplugin=input`. Then:

```bash
sudo systemctl daemon-reload
sudo systemctl restart bluetooth
```

**Option B – one-off run (for testing)**

```bash
sudo systemctl stop bluetooth
sudo /usr/libexec/bluetooth/bluetoothd --noplugin=input &
```

Bluetooth will stop when you kill that process or reboot. Use Option A for a permanent fix.

### Bluetooth Not Working

- Ensure Bluetooth is enabled: `bluetoothctl show`
- Check BlueZ is running: `systemctl status bluetooth`

### Device Not Discoverable

- Ensure the application is running and "Share" is active
- Check Bluetooth is enabled on both devices
- Try restarting Bluetooth: `sudo systemctl restart bluetooth`

## Architecture

The application consists of several components:

- **GUI** (`src/gui.py`): Tkinter interface for controlling sharing
- **Input Grabber** (`src/input_grabber.py`): Captures keyboard/mouse events using evdev
- **Bluetooth HID** (`src/bluetooth_hid.py`): Manages Bluetooth HID profile via BlueZ D-Bus API
- **HID Reports** (`src/hid_reports.py`): Converts evdev events to USB HID report format

## License

EasyHID is provided as-is for educational and personal use.
