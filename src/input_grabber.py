"""Input device grabbing and event capture using evdev"""

import threading
import logging
from typing import Optional, Callable, List
from evdev import InputDevice, list_devices, ecodes, categorize
from src.constants import KEY_LEFTSHIFT, KEY_SPACE, KEY_RIGHTSHIFT

logger = logging.getLogger(__name__)


class InputGrabber:
    """Manages exclusive input device grabbing and event forwarding"""
    
    def __init__(self, keyboard_callback: Optional[Callable[[int, int], None]] = None,
                 mouse_button_callback: Optional[Callable[[int, int], None]] = None,
                 mouse_move_callback: Optional[Callable[[int, int, int], None]] = None,
                 escape_callback: Optional[Callable[[], None]] = None):
        """
        Initialize input grabber.
        
        Args:
            keyboard_callback: Called with (key_code, value) for keyboard events
            mouse_button_callback: Called with (button_code, value) for mouse button events
            mouse_move_callback: Called with (rel_x, rel_y, rel_wheel) for mouse movement
            escape_callback: Called when escape combination is detected
        """
        self.keyboard_callback = keyboard_callback
        self.mouse_button_callback = mouse_button_callback
        self.mouse_move_callback = mouse_move_callback
        self.escape_callback = escape_callback
        
        self.keyboard_device: Optional[InputDevice] = None
        self.mouse_device: Optional[InputDevice] = None
        
        self.grabbed_devices: List[InputDevice] = []
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        self.active_keys = set()
    
    def find_devices(self) -> tuple[Optional[str], Optional[str]]:
        """
        Find keyboard and mouse devices.
        
        Returns:
            Tuple of (keyboard_path, mouse_path) or (None, None) if not found
        """
        devices = [InputDevice(path) for path in list_devices()]
        
        keyboard_path = None
        mouse_path = None
        
        for device in devices:
            try:
                caps = device.capabilities()
                
                # Check if it's a keyboard (has EV_KEY and KEY events)
                if ecodes.EV_KEY in caps:
                    keys = caps[ecodes.EV_KEY]
                    # Check if it has keyboard-like keys (not just mouse buttons)
                    has_keyboard_keys = any(
                        key in keys for key in [
                            ecodes.KEY_A, ecodes.KEY_B, ecodes.KEY_C,
                            ecodes.KEY_1, ecodes.KEY_2, ecodes.KEY_ENTER
                        ]
                    )
                    has_mouse_buttons = any(
                        key in keys for key in [
                            ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE
                        ]
                    )
                    
                    if has_keyboard_keys and not has_mouse_buttons:
                        if keyboard_path is None:
                            keyboard_path = device.path
                            logger.info(f"Found keyboard: {device.name} at {device.path}")
                    elif has_mouse_buttons:
                        if mouse_path is None:
                            mouse_path = device.path
                            logger.info(f"Found mouse: {device.name} at {device.path}")
            except (OSError, PermissionError) as e:
                logger.warning(f"Could not access device {device.path}: {e}")
                continue
        
        return keyboard_path, mouse_path
    
    def grab_devices(self) -> bool:
        """
        Grab keyboard and mouse devices exclusively.
        
        Returns:
            True if successful, False otherwise
        """
        keyboard_path, mouse_path = self.find_devices()
        
        if not keyboard_path:
            logger.error("No keyboard device found")
            return False
        
        try:
            # Grab keyboard
            self.keyboard_device = InputDevice(keyboard_path)
            self.keyboard_device.grab()
            self.grabbed_devices.append(self.keyboard_device)
            logger.info(f"Grabbed keyboard: {self.keyboard_device.name}")
            
            # Grab mouse if found
            if mouse_path:
                self.mouse_device = InputDevice(mouse_path)
                self.mouse_device.grab()
                self.grabbed_devices.append(self.mouse_device)
                logger.info(f"Grabbed mouse: {self.mouse_device.name}")
            
            return True
            
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to grab devices: {e}")
            self.release_devices()
            return False
    
    def release_devices(self):
        """Release all grabbed devices"""
        for device in self.grabbed_devices:
            try:
                device.ungrab()
                logger.info(f"Released device: {device.name}")
            except Exception as e:
                logger.warning(f"Error releasing device {device.path}: {e}")
        
        self.grabbed_devices.clear()
        self.keyboard_device = None
        self.mouse_device = None
    
    def start_capture(self):
        """Start capturing input events in a background thread"""
        if self.running:
            return
        
        if not self.keyboard_device:
            logger.error("No devices grabbed, cannot start capture")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info("Started input capture")
    
    def stop_capture(self):
        """Stop capturing input events"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("Stopped input capture")
    
    def _capture_loop(self):
        """Main event capture loop"""
        
        try:
            # Process events from both keyboard and mouse devices
            devices = []
            if self.keyboard_device:
                devices.append(('keyboard', self.keyboard_device))
            if self.mouse_device:
                devices.append(('mouse', self.mouse_device))
            
            if not devices:
                logger.error("No devices available for capture")
                return
            
            # Use select to monitor multiple devices
            while self.running:
                try:
                    # Get file descriptors for select
                    fds = [device.fd for _, device in devices]
                    
                    # Wait for events (with timeout to allow checking self.running)
                    ready, _, _ = select.select(fds, [], [], 0.1)
                    
                    if not ready:
                        continue
                    
                    # Process events from ready devices
                    for device_type, device in devices:
                        if device.fd not in ready:
                            continue
                        
                        try:
                            # Read available events
                            for event in device.read():
                                if not self.running:
                                    break
                                
                                if device_type == 'keyboard':
                                    self._process_keyboard_event(event)
                                elif device_type == 'mouse':
                                    self._process_mouse_event(event)
                        except BlockingIOError:
                            # No more events available
                            continue
                        except OSError as e:
                            # Device disconnected
                            logger.warning(f"Device {device.path} disconnected: {e}")
                            break
                    
                except Exception as e:
                    if self.running:  # Only log if we're still supposed to be running
                        logger.error(f"Error in capture loop: {e}")
                    break
        except Exception as e:
            logger.error(f"Error in capture loop: {e}")
        finally:
            self.running = False
    
    def _process_keyboard_event(self, event):
        """Process a keyboard event"""
        if event.type == ecodes.EV_KEY:
            key_code = event.code
            value = event.value
            
            # Update active keys for escape detection
            if value == 0:  # Released
                self.active_keys.discard(key_code)
            elif value == 1:  # Pressed
                self.active_keys.add(key_code)
            
            # Check for escape combination
            if self._check_escape_combo():
                if self.escape_callback:
                    self.escape_callback()
                return
            
            # Forward to callback
            if self.keyboard_callback:
                self.keyboard_callback(key_code, value)
        
        elif event.type == ecodes.EV_REL and self.mouse_device is None:
            # Handle mouse movement on keyboard device (for trackpads)
            self._accumulate_mouse_movement(event)
    
    def _process_mouse_event(self, event):
        """Process a mouse event"""
        if event.type == ecodes.EV_KEY:
            # Mouse button event
            button_code = event.code
            value = event.value
            if self.mouse_button_callback:
                self.mouse_button_callback(button_code, value)
        
        elif event.type == ecodes.EV_REL:
            # Mouse movement event
            self._accumulate_mouse_movement(event)
    
    def _accumulate_mouse_movement(self, event):
        """Accumulate mouse movement and send when complete"""
        # For simplicity, send each movement event immediately
        # A more sophisticated implementation could accumulate deltas
        if event.code == ecodes.REL_X:
            if self.mouse_move_callback:
                self.mouse_move_callback(event.value, 0, 0)
        elif event.code == ecodes.REL_Y:
            if self.mouse_move_callback:
                self.mouse_move_callback(0, event.value, 0)
        elif event.code == ecodes.REL_WHEEL:
            if self.mouse_move_callback:
                self.mouse_move_callback(0, 0, event.value)
    
    def _check_escape_combo(self) -> bool:
        """Check if escape combination is active"""
        return (
            KEY_LEFTSHIFT in self.active_keys and
            KEY_SPACE in self.active_keys and
            KEY_RIGHTSHIFT in self.active_keys
        )
