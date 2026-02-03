#!/usr/bin/env python3
"""Main entry point for EasyHID"""

import sys
import logging
import threading
import signal
from src.gui import SharingGUI
from src.input_grabber import InputGrabber
from src.bluetooth_hid import BluetoothHID
from src.hid_reports import HIDReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SharingApp:
    """Main application controller"""
    
    def __init__(self):
        self.gui = SharingGUI(
            share_callback=self.start_sharing,
            stop_callback=self.stop_sharing
        )
        
        self.input_grabber: InputGrabber = None
        self.bluetooth_hid: BluetoothHID = None
        self.hid_reports: HIDReportGenerator = None
        
        self.is_sharing = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal")
        self.stop_sharing()
        self.gui.quit()
        sys.exit(0)
    
    def start_sharing(self):
        """Start sharing keyboard and mouse"""
        if self.is_sharing:
            logger.warning("Already sharing")
            return
        
        logger.info("Starting sharing...")
        self.gui.set_sharing(True, "Initializing...")
        
        try:
            # Initialize HID report generator
            self.hid_reports = HIDReportGenerator()
            
            # Initialize Bluetooth HID
            self.bluetooth_hid = BluetoothHID()
            
            # Register HID profile
            ok, err_msg = self.bluetooth_hid.register_profile()
            if not ok:
                self.gui.update_status("Error: " + (err_msg or "Failed to register Bluetooth profile"))
                self.gui.set_sharing(False)
                return
            
            # Start D-Bus main loop
            self.bluetooth_hid.start_mainloop()
            
            # Set adapter to discoverable
            if not self.bluetooth_hid.set_discoverable(True):
                self.gui.update_status("Warning: Could not set adapter discoverable")
                logger.warning("Could not set adapter discoverable")
            
            # Initialize input grabber with callbacks
            self.input_grabber = InputGrabber(
                keyboard_callback=self._on_keyboard_event,
                mouse_button_callback=self._on_mouse_button_event,
                mouse_move_callback=self._on_mouse_move_event,
                escape_callback=self._on_escape_combo
            )
            
            # Grab input devices
            if not self.input_grabber.grab_devices():
                self.gui.update_status("Error: Failed to grab input devices. Check permissions.")
                logger.error("Failed to grab input devices")
                self.stop_sharing()
                return
            
            # Start capturing input
            self.input_grabber.start_capture()
            
            self.is_sharing = True
            self.gui.set_sharing(True, "Ready. Waiting for Bluetooth connection...")
            logger.info("Sharing started successfully")
            
        except Exception as e:
            logger.error(f"Error starting sharing: {e}", exc_info=True)
            self.gui.update_status(f"Error: {str(e)}")
            self.stop_sharing()
    
    def stop_sharing(self):
        """Stop sharing keyboard and mouse"""
        if not self.is_sharing:
            return
        
        logger.info("Stopping sharing...")
        self.is_sharing = False
        
        try:
            # Stop input capture
            if self.input_grabber:
                self.input_grabber.stop_capture()
                self.input_grabber.release_devices()
                self.input_grabber = None
            
            # Unregister Bluetooth profile
            if self.bluetooth_hid:
                self.bluetooth_hid.set_discoverable(False)
                self.bluetooth_hid.unregister_profile()
                self.bluetooth_hid.stop_mainloop()
                self.bluetooth_hid = None
            
            # Reset HID reports
            if self.hid_reports:
                self.hid_reports.reset()
                self.hid_reports = None
            
            self.gui.set_sharing(False, "Stopped")
            logger.info("Sharing stopped")
            
        except Exception as e:
            logger.error(f"Error stopping sharing: {e}", exc_info=True)
            self.gui.update_status(f"Error stopping: {str(e)}")
    
    def _on_keyboard_event(self, key_code: int, value: int):
        """Handle keyboard event"""
        if not self.is_sharing or not self.hid_reports or not self.bluetooth_hid:
            return
        
        try:
            report = self.hid_reports.process_keyboard_event(key_code, value)
            if report:
                self.bluetooth_hid.send_keyboard_report(report)
        except Exception as e:
            logger.error(f"Error processing keyboard event: {e}")
    
    def _on_mouse_button_event(self, button_code: int, value: int):
        """Handle mouse button event"""
        if not self.is_sharing or not self.hid_reports or not self.bluetooth_hid:
            return
        
        try:
            report = self.hid_reports.process_mouse_event(button_code, value)
            if report:
                self.bluetooth_hid.send_mouse_report(report)
        except Exception as e:
            logger.error(f"Error processing mouse button event: {e}")
    
    def _on_mouse_move_event(self, rel_x: int, rel_y: int, rel_wheel: int = 0):
        """Handle mouse movement event"""
        if not self.is_sharing or not self.hid_reports or not self.bluetooth_hid:
            return
        
        try:
            report = self.hid_reports.process_mouse_movement(rel_x, rel_y, rel_wheel)
            if report:
                self.bluetooth_hid.send_mouse_report(report)
        except Exception as e:
            logger.error(f"Error processing mouse movement: {e}")
    
    def _on_escape_combo(self):
        """Handle escape combination detection"""
        logger.info("Escape combination detected")
        self.stop_sharing()
    
    def run(self):
        """Run the application"""
        try:
            self.gui.run()
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.stop_sharing()


def main():
    """Main entry point"""
    app = SharingApp()
    app.run()


if __name__ == "__main__":
    main()
