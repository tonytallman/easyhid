"""Bluetooth HID profile implementation using BlueZ D-Bus API"""

import dbus
import dbus.service
import dbus.mainloop.glib
import dbus.exceptions
import logging
import socket
import struct
from typing import Optional, Callable
from gi.repository import GLib

logger = logging.getLogger(__name__)

# Message shown when HID UUID is already taken (e.g. by BlueZ input plugin)
UUID_ALREADY_REGISTERED_MSG = (
    "The HID Bluetooth profile is already in use (often by BlueZ's input plugin). "
    "To use this app, run bluetoothd with the input plugin disabled. "
    "See README 'Bluetooth HID already registered' for steps."
)

# D-Bus interfaces
BLUEZ_SERVICE = 'org.bluez'
BLUEZ_PROFILE_MANAGER = 'org.bluez.ProfileManager1'
BLUEZ_ADAPTER = 'org.bluez.Adapter1'
BLUEZ_DEVICE = 'org.bluez.Device1'
BLUEZ_PROFILE = 'org.bluez.Profile1'

# HID Profile UUID
HID_PROFILE_UUID = '00001124-0000-1000-8000-00805f9b34fb'

# HID Service Record (SDP record)
HID_SDP_RECORD = """
<?xml version="1.0" encoding="UTF-8" ?>
<record>
  <attribute id="0x0001">
    <sequence>
      <uuid value="0x1124"/>
    </sequence>
  </attribute>
  <attribute id="0x0004">
    <sequence>
      <sequence>
        <uuid value="0x0100"/>
      </sequence>
      <sequence>
        <uuid value="0x0003"/>
        <uint8 value="0x0c" name="channel"/>
      </sequence>
      <sequence>
        <uuid value="0x0005"/>
      </sequence>
    </sequence>
  </attribute>
  <attribute id="0x0005">
    <sequence>
      <uuid value="0x1002"/>
    </sequence>
  </attribute>
  <attribute id="0x0009">
    <sequence>
      <sequence>
        <uuid value="0x1124"/>
        <uint16 value="0x0100"/>
      </sequence>
    </sequence>
  </attribute>
  <attribute id="0x000d">
    <sequence>
      <sequence>
        <sequence>
          <uuid value="0x0100"/>
        </sequence>
        <sequence>
          <uuid value="0x0003"/>
          <uint8 value="0x0c" name="channel"/>
        </sequence>
      </sequence>
    </sequence>
  </attribute>
  <attribute id="0x0100">
    <text value="EasyHID" name="name"/>
  </attribute>
  <attribute id="0x0101">
    <text value="HID Device" name="description"/>
  </attribute>
  <attribute id="0x0102">
    <text value="Linux" name="provider"/>
  </attribute>
</record>
"""


class HIDProfile(dbus.service.Object):
    """BlueZ HID Profile implementation"""
    
    def __init__(self, bus, path, report_callback: Optional[Callable[[bytes], None]] = None):
        """
        Initialize HID Profile.
        
        Args:
            bus: D-Bus system bus
            path: Object path for this profile
            report_callback: Called when HID reports need to be sent
        """
        dbus.service.Object.__init__(self, bus, path)
        self.bus = bus
        self.report_callback = report_callback
        self.connected_devices = {}  # device_path -> (control_fd, interrupt_fd)
        self.mainloop = None
    
    @dbus.service.method(BLUEZ_PROFILE, in_signature='oha{sv}', out_signature='')
    def NewConnection(self, path, fd, properties):
        """Called when a new device connects"""
        logger.info(f"New HID connection from {path}")
        device_path = str(path)
        
        # Get file descriptor
        fd_obj = fd.take()
        fd_socket = socket.fromfd(fd_obj, socket.AF_UNIX, socket.SOCK_STREAM)
        
        # For HID, we typically need two channels: control and interrupt
        # This is a simplified implementation
        self.connected_devices[device_path] = fd_socket
        logger.info(f"Device {device_path} connected")
    
    @dbus.service.method(BLUEZ_PROFILE, in_signature='o', out_signature='')
    def RequestDisconnection(self, path):
        """Called when device disconnects"""
        device_path = str(path)
        if device_path in self.connected_devices:
            try:
                self.connected_devices[device_path].close()
            except:
                pass
            del self.connected_devices[device_path]
            logger.info(f"Device {device_path} disconnected")
    
    @dbus.service.method(BLUEZ_PROFILE, in_signature='', out_signature='')
    def Release(self):
        """Called when profile is released"""
        logger.info("HID Profile released")
        for device_path in list(self.connected_devices.keys()):
            self.RequestDisconnection(device_path)
    
    def send_report(self, report_data: bytes):
        """Send HID report to all connected devices"""
        for device_path, socket_fd in self.connected_devices.items():
            try:
                socket_fd.sendall(report_data)
            except Exception as e:
                logger.error(f"Error sending report to {device_path}: {e}")


class BluetoothHID:
    """Manages Bluetooth HID device functionality"""
    
    def __init__(self, device_name: str = "EasyHID"):
        """
        Initialize Bluetooth HID manager.
        
        Args:
            device_name: Name to advertise as Bluetooth device
        """
        self.device_name = device_name
        self.bus = None
        self.profile = None
        self.profile_manager = None
        self.adapter = None
        self.adapter_path = None
        self.mainloop = None
        self.connected = False
        
        # Initialize D-Bus
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
    
    def register_profile(self) -> tuple[bool, Optional[str]]:
        """Register HID profile with BlueZ. Returns (success, error_message_for_user)."""
        try:
            # Get ProfileManager
            self.profile_manager = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE, '/org/bluez'),
                BLUEZ_PROFILE_MANAGER
            )
            
            # Create profile object
            profile_path = '/org/bluez/hid/profile'
            self.profile = HIDProfile(self.bus, profile_path, self._on_report_needed)
            
            # Register profile
            opts = {
                'Name': 'HID',
                'Service': HID_PROFILE_UUID,
                'Role': 'server',
                'RequireAuthentication': False,
                'RequireAuthorization': False,
            }
            
            self.profile_manager.RegisterProfile(profile_path, HID_PROFILE_UUID, opts)
            logger.info("HID Profile registered")
            return True, None
            
        except dbus.exceptions.DBusException as e:
            if "already registered" in str(e).lower() or (
                getattr(e, "get_dbus_name", lambda: "")() == "org.bluez.Error.NotPermitted"
            ):
                logger.error("Failed to register HID profile: %s", e)
                logger.error(UUID_ALREADY_REGISTERED_MSG)
                return False, "HID profile in use. Disable BlueZ input plugin (see README)."
            else:
                logger.error("Failed to register HID profile: %s", e)
                return False, str(e)
        except Exception as e:
            logger.error("Failed to register HID profile: %s", e)
            return False, str(e)
    
    def unregister_profile(self):
        """Unregister HID profile"""
        if self.profile_manager and self.profile:
            try:
                profile_path = '/org/bluez/hid/profile'
                self.profile_manager.UnregisterProfile(profile_path)
                logger.info("HID Profile unregistered")
            except Exception as e:
                logger.error(f"Failed to unregister profile: {e}")
    
    def set_discoverable(self, discoverable: bool = True) -> bool:
        """Set adapter to discoverable mode"""
        try:
            # Find adapter
            obj_manager = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE, '/'),
                'org.freedesktop.DBus.ObjectManager'
            )
            
            objects = obj_manager.GetManagedObjects()
            for path, interfaces in objects.items():
                if BLUEZ_ADAPTER in interfaces:
                    self.adapter_path = path
                    break
            
            if not self.adapter_path:
                logger.error("No Bluetooth adapter found")
                return False
            
            # Get adapter interface
            self.adapter = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE, self.adapter_path),
                BLUEZ_ADAPTER
            )
            
            # Set discoverable
            self.adapter.SetProperty('Discoverable', discoverable)
            if discoverable:
                self.adapter.SetProperty('Pairable', True)
            
            logger.info(f"Adapter discoverable: {discoverable}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set discoverable: {e}")
            return False
    
    def _on_report_needed(self, report_data: bytes):
        """Callback when report needs to be sent"""
        pass
    
    def send_keyboard_report(self, report: bytes):
        """Send keyboard HID report"""
        if self.profile:
            self.profile.send_report(report)
    
    def send_mouse_report(self, report: bytes):
        """Send mouse HID report"""
        if self.profile:
            self.profile.send_report(report)
    
    def start_mainloop(self):
        """Start GLib main loop for D-Bus events"""
        self.mainloop = GLib.MainLoop()
        # Run in a separate thread
        import threading
        thread = threading.Thread(target=self.mainloop.run, daemon=True)
        thread.start()
    
    def stop_mainloop(self):
        """Stop GLib main loop"""
        if self.mainloop:
            self.mainloop.quit()
