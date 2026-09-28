"""
ArduinoMouse — HID communication module.

Communicates with Arduino Leonardo via vendor-specific HID feature reports.
No Serial/COM port used. Device is found by VID/PID.

Protocol (feature report, 8 bytes):
  Byte 0: Command
    0xb7 = Ping (device echoes back 0xb7)
    0x01 = Move (byte1=X, byte2=Y as signed int8)
    0x02 = Click (byte1=button mask)
    0x03 = Press (byte1=button mask)
    0x04 = Release (byte1=button mask)
  Bytes 1-7: Parameters (zero-padded)
"""

import hid
import sys
import time
from termcolor import colored

# Device identifiers — Razer VID/PID
DEVICE_VID = 0x1532
DEVICE_PID = 0x0091

# Command bytes
CMD_PING    = 0xb7
CMD_MOVE    = 0x01
CMD_CLICK   = 0x02
CMD_PRESS   = 0x03
CMD_RELEASE = 0x04

# HID report config (must match Arduino CommandChannel)
REPORT_ID   = 0x03
REPORT_SIZE = 8

# Button masks (match Arduino ImprovedMouse.h)
MOUSE_LEFT   = 1
MOUSE_RIGHT  = 2
MOUSE_MIDDLE = 4


class ArduinoMouse:
    def __init__(self):
        self.device = None
        self._connect()
        self._ping()

    def _connect(self):
        """Find and open the Arduino HID device by VID/PID.
        
        IMPORTANT: We must open ONLY the vendor-specific interface (usage_page 0xFF00),
        NOT the mouse interface (usage_page 0x01). Opening the mouse interface will
        block physical mouse buttons from reaching Windows.
        """
        try:
            # Enumerate ALL HID devices with our VID/PID
            devices = hid.enumerate(DEVICE_VID, DEVICE_PID)

            if not devices:
                print(colored('[Error]', 'red'),
                      colored(f'No HID device found with VID={hex(DEVICE_VID)} PID={hex(DEVICE_PID)}.', 'white'))
                print(colored('[Info]', 'yellow'),
                      colored('Make sure Arduino is flashed with the Invinciblx777 board profile.', 'white'))
                print(colored('[Info]', 'yellow'),
                      colored('Check Device Manager for "Razer Viper" under HID devices.', 'white'))
                sys.exit(1)

            # Debug: print all found interfaces
            print(colored('[Debug]', 'cyan'),
                  colored(f'Found {len(devices)} HID interface(s) with VID={hex(DEVICE_VID)} PID={hex(DEVICE_PID)}:', 'white'))
            for i, dev in enumerate(devices):
                up = dev.get('usage_page', 0)
                u = dev.get('usage', 0)
                iface = dev.get('interface_number', -1)
                prod = dev.get('product_string', 'Unknown')
                print(colored(f'  [{i}]', 'cyan'),
                      colored(f'Interface={iface}  UsagePage={hex(up)}  Usage={hex(u)}  Product="{prod}"', 'white'))

            # STRICTLY find the vendor-specific interface (usage_page 0xFF00)
            # NEVER open usage_page 0x01 (Generic Desktop / Mouse) — that kills mouse buttons
            target = None
            for dev in devices:
                up = dev.get('usage_page', 0)
                if up == 0xFF00:  # Vendor-specific
                    target = dev
                    break

            if target is None:
                # Second pass: try any interface that is NOT a mouse (usage_page != 0x01)
                for dev in devices:
                    up = dev.get('usage_page', 0)
                    usage = dev.get('usage', 0)
                    if up != 0x01 and usage != 0x02:  # Not Generic Desktop / Mouse
                        target = dev
                        break

            if target is None:
                print(colored('[Error]', 'red'),
                      colored('Could not find the vendor-specific command channel interface.', 'white'))
                print(colored('[Info]', 'yellow'),
                      colored('Only mouse interfaces were found. The CommandChannel may not be', 'white'))
                print(colored('[Info]', 'yellow'),
                      colored('registered correctly. Re-flash Arduino with the Invinciblx777 board profile.', 'white'))
                print(colored('[Info]', 'yellow'),
                      colored('Refusing to open the mouse interface (would block your mouse buttons).', 'white'))
                sys.exit(1)

            self.device = hid.device()
            self.device.open_path(target['path'])
            self.device.set_nonblocking(True)

            print(colored('[Info]', 'green'),
                  colored(f'Connected to HID device:', 'white'),
                  colored(f'{target.get("manufacturer_string", "Unknown")} '
                          f'{target.get("product_string", "Unknown")}', 'magenta'))
            print(colored('[Info]', 'green'),
                  colored(f'Interface: {target.get("interface_number", "?")} '
                          f'Usage Page: {hex(target.get("usage_page", 0))}', 'white'))

        except Exception as e:
            print(colored('[Error]', 'red'),
                  colored(f'Failed to connect to HID device: {e}', 'white'))
            sys.exit(1)

    def _ping(self):
        """Send ping (0xb7) and verify device responds."""
        try:
            # Send ping as feature report
            # Format: [report_id, CMD_PING, 0, 0, 0, 0, 0, 0, 0]
            report = [REPORT_ID] + [CMD_PING] + [0] * (REPORT_SIZE - 1)
            self.device.send_feature_report(report)

            # Small delay for Arduino to process
            time.sleep(0.02)

            # Read response
            response = self.device.get_feature_report(REPORT_ID, REPORT_SIZE + 1)

            if response and len(response) > 1 and response[1] == CMD_PING:
                print(colored('[Info]', 'green'),
                      colored('Ping 0xb7 — Device alive ✓', 'cyan'))
            else:
                print(colored('[Warning]', 'yellow'),
                      colored(f'Ping response: {response}', 'white'))
                print(colored('[Warning]', 'yellow'),
                      colored('Device may not be running correct firmware.', 'white'))

        except Exception as e:
            print(colored('[Warning]', 'yellow'),
                  colored(f'Ping failed (non-fatal): {e}', 'white'))

    def _send_command(self, cmd, param1=0, param2=0, param3=0):
        """Send a command via HID feature report. Ultra low latency."""
        if self.device is None:
            return
        try:
            # Feature report: [report_id, cmd, p1, p2, p3, 0, 0, 0, 0]
            report = [REPORT_ID, cmd,
                      param1 & 0xFF,
                      param2 & 0xFF,
                      param3 & 0xFF,
                      0, 0, 0, 0]
            self.device.send_feature_report(report)
        except Exception:
            pass  # Silently handle transient USB errors

    def move(self, x, y):
        """Send relative mouse movement. x,y are signed int8 (-127 to 127)."""
        # Clamp to int8 range
        x = max(-127, min(127, int(x)))
        y = max(-127, min(127, int(y)))
        # Convert to unsigned byte representation for transport
        x_byte = x & 0xFF
        y_byte = y & 0xFF
        self._send_command(CMD_MOVE, x_byte, y_byte)

    def click(self, button=MOUSE_LEFT):
        """Click (press + release) a mouse button."""
        self._send_command(CMD_CLICK, button)

    def press(self, button=MOUSE_LEFT):
        """Press and hold a mouse button."""
        self._send_command(CMD_PRESS, button)

    def release(self, button=MOUSE_LEFT):
        """Release a mouse button."""
        self._send_command(CMD_RELEASE, button)

    def close(self):
        """Close HID device connection."""
        if self.device is not None:
            try:
                self.device.close()
            except Exception:
                pass
            self.device = None

    def __del__(self):
        self.close()
