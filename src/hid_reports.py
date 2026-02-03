"""HID report generation for keyboard and mouse events"""

from typing import Optional, Dict, Set
from src.constants import (
    EVDEV_TO_HID_KEYCODES,
    EVDEV_TO_MOUSE_BUTTON,
    HID_KEYBOARD_REPORT_SIZE,
    HID_MOUSE_REPORT_SIZE,
    KEY_LEFTSHIFT,
    KEY_RIGHTSHIFT,
    KEY_SPACE,
)


class HIDReportGenerator:
    """Generates USB HID reports from evdev events"""
    
    def __init__(self):
        self.active_keys: Set[int] = set()
        self.modifier_state = 0
        self.mouse_buttons = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_wheel = 0
        
    def process_keyboard_event(self, key_code: int, value: int) -> Optional[bytes]:
        """
        Process a keyboard event and generate HID report if needed.
        
        Args:
            key_code: evdev key code
            value: 0 = released, 1 = pressed, 2 = held
            
        Returns:
            HID keyboard report bytes or None if no report needed
        """
        if value == 0:  # Key released
            if key_code in self.active_keys:
                self.active_keys.remove(key_code)
        elif value == 1:  # Key pressed
            self.active_keys.add(key_code)
        elif value == 2:  # Key held (repeat)
            # Already tracked, no change needed
            pass
        
        # Update modifier state
        self._update_modifiers()
        
        # Generate report
        return self._generate_keyboard_report()
    
    def process_mouse_event(self, button_code: int, value: int) -> Optional[bytes]:
        """
        Process a mouse button event.
        
        Args:
            button_code: evdev button code
            value: 0 = released, 1 = pressed
            
        Returns:
            HID mouse report bytes or None
        """
        if button_code in EVDEV_TO_MOUSE_BUTTON:
            button_mask = EVDEV_TO_MOUSE_BUTTON[button_code]
            if value == 1:  # Pressed
                self.mouse_buttons |= button_mask
            elif value == 0:  # Released
                self.mouse_buttons &= ~button_mask
        
        return self._generate_mouse_report()
    
    def process_mouse_movement(self, rel_x: int, rel_y: int, rel_wheel: int = 0) -> bytes:
        """
        Process mouse movement and generate HID report.
        
        Args:
            rel_x: Relative X movement
            rel_y: Relative Y movement
            rel_wheel: Relative wheel movement
            
        Returns:
            HID mouse report bytes
        """
        self.mouse_x = rel_x
        self.mouse_y = rel_y
        self.mouse_wheel = rel_wheel
        
        return self._generate_mouse_report()
    
    def _update_modifiers(self):
        """Update modifier byte based on active keys"""
        self.modifier_state = 0
        
        if KEY_LEFTSHIFT in self.active_keys or KEY_RIGHTSHIFT in self.active_keys:
            # Check which shift is pressed
            if KEY_LEFTSHIFT in self.active_keys:
                self.modifier_state |= 0x02  # Left Shift
            if KEY_RIGHTSHIFT in self.active_keys:
                self.modifier_state |= 0x20  # Right Shift
        
        # Map other modifiers if needed
        # Left Control (29), Right Control (97)
        # Left Alt (56), Right Alt (100)
        # Left Meta (125), Right Meta (126)
        for key_code in self.active_keys:
            if key_code == 29:  # Left Control
                self.modifier_state |= 0x01
            elif key_code == 97:  # Right Control
                self.modifier_state |= 0x10
            elif key_code == 56:  # Left Alt
                self.modifier_state |= 0x04
            elif key_code == 100:  # Right Alt
                self.modifier_state |= 0x40
            elif key_code == 125:  # Left Meta
                self.modifier_state |= 0x08
            elif key_code == 126:  # Right Meta
                self.modifier_state |= 0x80
    
    def _generate_keyboard_report(self) -> bytes:
        """
        Generate HID keyboard report.
        Format: [modifier, reserved, key1, key2, key3, key4, key5, key6]
        """
        report = bytearray(HID_KEYBOARD_REPORT_SIZE)
        report[0] = self.modifier_state & 0xFF
        
        # Convert active keys to HID keycodes
        hid_keys = []
        for evdev_code in self.active_keys:
            # Skip modifiers (they're in modifier byte)
            if evdev_code in (KEY_LEFTSHIFT, KEY_RIGHTSHIFT, 29, 97, 56, 100, 125, 126):
                continue
            
            if evdev_code in EVDEV_TO_HID_KEYCODES:
                hid_key = EVDEV_TO_HID_KEYCODES[evdev_code]
                if hid_key not in hid_keys:
                    hid_keys.append(hid_key)
        
        # Fill key slots (max 6 keys)
        for i, hid_key in enumerate(hid_keys[:6]):
            report[2 + i] = hid_key
        
        return bytes(report)
    
    def _generate_mouse_report(self) -> bytes:
        """
        Generate HID mouse report.
        Format: [buttons, x, y, wheel]
        """
        report = bytearray(HID_MOUSE_REPORT_SIZE)
        report[0] = self.mouse_buttons & 0xFF
        report[1] = self._clamp_mouse_delta(self.mouse_x)
        report[2] = self._clamp_mouse_delta(self.mouse_y)
        report[3] = self._clamp_mouse_delta(self.mouse_wheel)
        
        # Reset deltas after generating report
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_wheel = 0
        
        return bytes(report)
    
    @staticmethod
    def _clamp_mouse_delta(value: int) -> int:
        """Clamp mouse delta to signed 8-bit range"""
        return max(-127, min(127, value))
    
    def check_escape_combo(self) -> bool:
        """
        Check if escape combination is active.
        Returns True if Left Shift + Space + Right Shift are all held.
        """
        return (
            KEY_LEFTSHIFT in self.active_keys and
            KEY_SPACE in self.active_keys and
            KEY_RIGHTSHIFT in self.active_keys
        )
    
    def reset(self):
        """Reset all state"""
        self.active_keys.clear()
        self.modifier_state = 0
        self.mouse_buttons = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_wheel = 0
