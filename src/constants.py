"""Constants for key codes, HID descriptors, and Bluetooth configuration"""

# Escape combination keys (evdev codes)
KEY_LEFTSHIFT = 42
KEY_SPACE = 57
KEY_RIGHTSHIFT = 54

# HID Usage Page constants
HID_USAGE_PAGE_GENERIC_DESKTOP = 0x01
HID_USAGE_PAGE_KEYBOARD = 0x07
HID_USAGE_PAGE_BUTTON = 0x09

# HID Usage constants
HID_USAGE_KEYBOARD = 0x06
HID_USAGE_MOUSE = 0x02
HID_USAGE_X = 0x30
HID_USAGE_Y = 0x31
HID_USAGE_WHEEL = 0x38

# HID Report sizes
HID_KEYBOARD_REPORT_SIZE = 8  # 1 modifier byte + 6 key bytes + 1 reserved
HID_MOUSE_REPORT_SIZE = 4  # 1 button byte + 1 X + 1 Y + 1 wheel

# Bluetooth HID Profile UUID
HID_SERVICE_UUID = "00001124-0000-1000-8000-00805f9b34fb"

# Device name for Bluetooth advertising
BLUETOOTH_DEVICE_NAME = "Linux Keyboard & Mouse"

# evdev to HID keycode mapping (common keys)
# This is a simplified mapping - full mapping would be extensive
EVDEV_TO_HID_KEYCODES = {
    # Letters (a-z)
    30: 4,   # a -> A
    31: 5,   # s -> S
    32: 6,   # d -> D
    33: 7,   # f -> F
    34: 8,   # g -> G
    35: 9,   # h -> H
    36: 10,  # j -> J
    37: 11,  # k -> K
    38: 12,  # l -> L
    39: 13,  # ; -> ;
    40: 14,  # ' -> '
    41: 15,  # ` -> `
    16: 16,  # q -> Q
    17: 17,  # w -> W
    18: 18,  # e -> E
    19: 19,  # r -> R
    20: 20,  # t -> T
    21: 21,  # y -> Y
    22: 22,  # u -> U
    23: 23,  # i -> I
    24: 24,  # o -> O
    25: 25,  # p -> P
    26: 26,  # [ -> [
    27: 27,  # ] -> ]
    43: 28,  # \ -> \
    44: 29,  # z -> Z
    45: 30,  # x -> X
    46: 31,  # c -> C
    47: 32,  # v -> V
    48: 33,  # b -> B
    49: 34,  # n -> N
    50: 35,  # m -> M
    51: 36,  # , -> ,
    52: 37,  # . -> .
    53: 38,  # / -> /
    
    # Numbers
    2: 30,   # 1 -> 1
    3: 31,   # 2 -> 2
    4: 32,   # 3 -> 3
    5: 33,   # 4 -> 4
    6: 34,   # 5 -> 5
    7: 35,   # 6 -> 6
    8: 36,   # 7 -> 7
    9: 37,   # 8 -> 8
    10: 38,  # 9 -> 9
    11: 39,  # 0 -> 0
    
    # Modifiers
    42: 0xE0,  # Left Shift
    54: 0xE1,  # Right Shift
    29: 0xE2,  # Left Control
    97: 0xE3,  # Right Control
    56: 0xE4,  # Left Alt
    100: 0xE5, # Right Alt
    125: 0xE6, # Left Meta/Super
    126: 0xE7, # Right Meta/Super
    
    # Special keys
    57: 0x2C,  # Space
    28: 0x28,  # Enter
    1: 0x29,   # Escape
    14: 0x2A,  # Backspace
    15: 0x2B,  # Tab
    58: 0x39,  # Caps Lock
    59: 0x3A,  # F1
    60: 0x3B,  # F2
    61: 0x3C,  # F3
    62: 0x3D,  # F4
    63: 0x3E,  # F5
    64: 0x3F,  # F6
    65: 0x40,  # F7
    66: 0x41,  # F8
    67: 0x42,  # F9
    68: 0x43,  # F10
    87: 0x44,  # F11
    88: 0x45,  # F12
    
    # Arrow keys
    103: 0x52, # Up
    108: 0x51, # Down
    105: 0x50, # Left
    106: 0x4F, # Right
}

# Mouse button mappings
MOUSE_BUTTON_LEFT = 0x01
MOUSE_BUTTON_RIGHT = 0x02
MOUSE_BUTTON_MIDDLE = 0x04

EVDEV_TO_MOUSE_BUTTON = {
    272: MOUSE_BUTTON_LEFT,    # BTN_LEFT
    273: MOUSE_BUTTON_RIGHT,   # BTN_RIGHT
    274: MOUSE_BUTTON_MIDDLE,  # BTN_MIDDLE
}
