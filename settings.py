"""
Settings loader for Invinciblx777 v2.0.

Loads settings.json from the same directory as this script.
Falls back to defaults if the file is missing or a key is absent.
"""

import json
import os
import sys
from termcolor import colored

# Resolve settings.json path relative to this script's directory
_SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
_SETTINGS_FILE = os.path.join(_SETTINGS_DIR, 'settings.json')

# ── Defaults ────────────────────────────────────────────────────
_DEFAULTS = {
    'screen': {
        'auto_detect': True,
        'width': 1920,
        'height': 1080,
    },
    'capture': {
        'fov': 50,
    },
    'aimbot': {
        'enabled': True,
        'activation_key': 'right_mouse',
        'speed': 0.25,
        'headshot_offset': 9,
        'min_pixels': 4,
    },
    'triggerbot': {
        'enabled': True,
        'activation_key': 'left_alt',
        'threshold_x': 4,
        'threshold_y': 10,
    },
    'color': {
        'lower_hue': 140,
        'upper_hue': 150,
        'lower_saturation': 110,
        'upper_saturation': 195,
        'lower_value': 150,
        'upper_value': 255,
    },
    'toggle_key': 'F1',
    'ui_refresh_rate': 60,
}

# Map friendly key names → win32 virtual-key codes
_KEY_MAP = {
    'right_mouse': 0x02,
    'left_mouse': 0x01,
    'middle_mouse': 0x04,
    'left_alt': 0x12,
    'right_alt': 0xA5,
    'left_shift': 0xA0,
    'right_shift': 0xA1,
    'left_ctrl': 0xA2,
    'right_ctrl': 0xA3,
    'x1_mouse': 0x05,
    'x2_mouse': 0x06,
}


def _deep_merge(defaults: dict, overrides: dict) -> dict:
    """Recursively merge overrides into defaults. Skip comment keys."""
    result = dict(defaults)
    for key, value in overrides.items():
        if key.startswith('//'):
            continue  # Skip JSON comments
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_settings() -> dict:
    """Load and validate settings from settings.json."""
    settings = dict(_DEFAULTS)

    if os.path.isfile(_SETTINGS_FILE):
        try:
            with open(_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                user = json.load(f)
            settings = _deep_merge(settings, user)
            print(colored('[Settings]', 'green'),
                  colored(f'Loaded from {os.path.basename(_SETTINGS_FILE)}', 'white'))
        except json.JSONDecodeError as e:
            print(colored('[Settings]', 'red'),
                  colored(f'JSON parse error in settings.json: {e}', 'white'))
            print(colored('[Settings]', 'yellow'),
                  colored('Using defaults.', 'white'))
        except Exception as e:
            print(colored('[Settings]', 'red'),
                  colored(f'Failed to load settings.json: {e}', 'white'))
            print(colored('[Settings]', 'yellow'),
                  colored('Using defaults.', 'white'))
    else:
        print(colored('[Settings]', 'yellow'),
              colored('settings.json not found — using defaults.', 'white'))

    # ── Validate & clamp ────────────────────────────────────────
    aim = settings['aimbot']
    aim['speed'] = max(0.05, min(1.0, float(aim['speed'])))
    aim['headshot_offset'] = max(0, int(aim['headshot_offset']))
    aim['min_pixels'] = max(1, int(aim['min_pixels']))

    trig = settings['triggerbot']
    trig['threshold_x'] = max(1, int(trig['threshold_x']))
    trig['threshold_y'] = max(1, int(trig['threshold_y']))

    cap = settings['capture']
    cap['fov'] = max(10, min(500, int(cap['fov'])))

    settings['ui_refresh_rate'] = max(10, min(240, int(settings['ui_refresh_rate'])))

    # Resolve activation key VK codes
    aim['vk_code'] = _KEY_MAP.get(aim['activation_key'], 0x02)
    trig['vk_code'] = _KEY_MAP.get(trig['activation_key'], 0x12)

    return settings
