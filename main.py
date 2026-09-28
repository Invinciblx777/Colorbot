"""
Invinciblx777 v2.0 — Ultra Low-Latency Color Aimbot

Features:
  - HID communication (no COM port, no Serial)
  - Razer VID/PID spoofing (0x1532/0x0091)
  - 0xb7 ping protocol for device discovery
  - DXGI Desktop Duplication screen capture (<1ms)
  - NumPy vectorized color detection (<0.5ms)
  - Real-time latency and FPS monitoring
  - Auto screen resolution detection
  - External settings.json configuration
"""

import os
import sys
import time
import ctypes
import keyboard
from termcolor import colored
from settings import load_settings
from invinciblx777 import Invinciblx777

# Force UTF-8 for console output to fix UnicodeEncodeError
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def get_screen_resolution():
    """Auto-detect primary monitor resolution."""
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        w = user32.GetSystemMetrics(0)
        h = user32.GetSystemMetrics(1)
        return w, h
    except Exception:
        return 1920, 1080  # Fallback


def main():
    os.system('title Invinciblx777 v2.0')
    os.system('cls')

    # ── Load settings ───────────────────────────────────────────
    settings = load_settings()

    fov = settings['capture']['fov']
    toggle_key = settings['toggle_key']
    ui_hz = settings['ui_refresh_rate']
    aim = settings['aimbot']
    trig = settings['triggerbot']
    col = settings['color']

    # ── Screen resolution ───────────────────────────────────────
    if settings['screen']['auto_detect']:
        screen_w, screen_h = get_screen_resolution()
    else:
        screen_w = settings['screen']['width']
        screen_h = settings['screen']['height']

    center_x = screen_w // 2
    center_y = screen_h // 2

    print(colored('''
                     ▄████▄   ▒█████   ██▓     ▒█████   ██▓     ▒█████   ██▀███   ▄▄▄       ███▄    █ ▄▄▄█████▓
                    ▒██▀ ▀█  ▒██▒  ██▒▓██▒    ▒██▒  ██▒▓██▒    ▒██▒  ██▒▓██ ▒ ██▒▒████▄     ██ ▀█   █ ▓  ██▒ ▓▒
                    ▒▓█    ▄ ▒██░  ██▒▒██░    ▒██░  ██▒▒██░    ▒██░  ██▒▓██ ░▄█ ▒▒██  ▀█▄  ▓██  ▀█ ██▒▒ ▓██░ ▒░
                    ▒▓▓▄ ▄██▒▒██   ██░▒██░    ▒██   ██░▒██░    ▒██   ██░▒██▀▀█▄  ░██▄▄▄▄██ ▓██▒  ▐▌██▒░ ▓██▓ ░ 
                    ▒ ▓███▀ ░░ ████▓▒░░██████▒░ ████▓▒░░██████▒░ ████▓▒░░██▓ ▒██▒ ▓█   ▓██▒▒██░   ▓██░  ▒██▒ ░ 
                    ░ ░▒ ▒  ░░ ▒░▒░▒░ ░ ▒░▓  ░░ ▒░▒░▒░ ░ ▒░▓  ░░ ▒░▒░▒░ ░ ▒▓ ░▒▓░ ▒▒   ▓▒█░░ ▒░   ▒ ▒   ▒ ░░   
                      ░  ▒     ░ ▒ ▒░ ░ ░ ▒  ░  ░ ▒ ▒░ ░ ░ ▒  ░  ░ ▒ ▒░   ░▒ ░ ▒░  ▒   ▒▒ ░░ ░░   ░ ▒░    ░    
                    ░        ░ ░ ░ ▒    ░ ░   ░ ░ ░ ▒    ░ ░   ░ ░ ░ ▒    ░░   ░   ░   ▒      ░   ░ ░   ░      
                    ░ ░          ░ ░      ░  ░    ░ ░      ░  ░    ░ ░     ░           ░  ░         ░          
                    ░                                                                                         
                                              COLOR AIMBOT — v2.0''', 'magenta'))

    print()
    print(colored('  ╔══════════════════════════════════════════════════════════════════╗', 'cyan'))
    print(colored('  ║', 'cyan'), colored(' HID Mode', 'green'), colored('│', 'cyan'),
          colored('No COM Port — Pure HID Communication            ', 'white'), colored('║', 'cyan'))
    print(colored('  ║', 'cyan'), colored(' Protocol', 'green'), colored('│', 'cyan'),
          colored('Ping 0xb7 — VID:0x1532 PID:0x0091               ', 'white'), colored('║', 'cyan'))
    print(colored('  ║', 'cyan'), colored(' Screen  ', 'green'), colored('│', 'cyan'),
          colored(f' {screen_w}x{screen_h} — FOV: {fov}px                            ', 'white')[:49],
          colored('║', 'cyan'))
    print(colored('  ╠══════════════════════════════════════════════════════════════════╣', 'cyan'))
    print(colored('  ║', 'cyan'), colored(' Aimbot  ', 'green'), colored('│', 'cyan'),
          colored(f' {"ON" if aim["enabled"] else "OFF"}  Speed: {aim["speed"]}  '
                  f'Head: {aim["headshot_offset"]}px  MinPx: {aim["min_pixels"]}', 'white')[:49],
          colored('║', 'cyan'))
    print(colored('  ║', 'cyan'), colored(' Trigger ', 'green'), colored('│', 'cyan'),
          colored(f' {"ON" if trig["enabled"] else "OFF"}  '
                  f'Thresh: {trig["threshold_x"]}x{trig["threshold_y"]}px', 'white')[:49],
          colored('║', 'cyan'))
    print(colored('  ║', 'cyan'), colored(' Color   ', 'green'), colored('│', 'cyan'),
          colored(f' H:{col["lower_hue"]}-{col["upper_hue"]}  '
                  f'S:{col["lower_saturation"]}-{col["upper_saturation"]}  '
                  f'V:{col["lower_value"]}-{col["upper_value"]}', 'white')[:49],
          colored('║', 'cyan'))
    print(colored('  ╠══════════════════════════════════════════════════════════════════╣', 'cyan'))
    print(colored('  ║', 'cyan'), colored(' Controls:                                                     ', 'white'), colored('║', 'cyan'))
    print(colored('  ║', 'cyan'), colored(f'   {toggle_key}', 'magenta'),
          colored('       — Toggle ON/OFF                                  ', 'white')[:54], colored('║', 'cyan'))
    print(colored('  ║', 'cyan'), colored(f'   {aim["activation_key"]}', 'magenta'),
          colored('— Aimbot                                          ', 'white')[:54], colored('║', 'cyan'))
    print(colored('  ║', 'cyan'), colored(f'   {trig["activation_key"]}', 'magenta'),
          colored('— Triggerbot                                      ', 'white')[:54], colored('║', 'cyan'))
    print(colored('  ╚══════════════════════════════════════════════════════════════════╝', 'cyan'))
    print()

    # ── Initialize Invinciblx777 engine ──────────────────────────────
    invinciblx777 = Invinciblx777(center_x - fov // 2, center_y - fov // 2, fov, settings)

    status = 'OFF'
    last_toggle = 0
    sleep_time = 1.0 / ui_hz

    try:
        while True:
            now = time.time()

            # Toggle with debounce
            if keyboard.is_pressed(toggle_key) and (now - last_toggle) > 0.3:
                invinciblx777.toggle()
                status = 'ON ' if invinciblx777.toggled else 'OFF'
                last_toggle = now

            # Status display with live stats
            status_color = 'green' if invinciblx777.toggled else 'red'
            fps_str = f'{invinciblx777.capture_fps:.0f}'
            lat_str = f'{invinciblx777.latency:.2f}ms'

            print(f'\r  {colored("[Status]", "green")} {colored(status, status_color)}'
                  f'  {colored("│", "cyan")} {colored("FPS:", "green")} {colored(fps_str, "white")}'
                  f'  {colored("│", "cyan")} {colored("Latency:", "green")} {colored(lat_str, "white")}   ',
                  end='')

            time.sleep(sleep_time)

    except (KeyboardInterrupt, SystemExit):
        print(colored('\n\n  [Info]', 'green'), colored('Shutting down...', 'white'))
    finally:
        invinciblx777.close()
        print(colored('  [Info]', 'green'), colored('Closed. GG ✓\n', 'white'))


if __name__ == '__main__':
    main()

