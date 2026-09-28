<div align="center">
  
# 🎯 Invinciblx777 v2.0
### Ultra Low-Latency Color Aimbot Engine

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-v2.0-success.svg)]()

<p align="center">
  A high-performance, next-generation computer vision aimbot and triggerbot using pure NumPy vectorized operations and DXGI Desktop Duplication. Built for absolute minimal latency (<1ms detection) and robust hardware-level spoofing.
</p>
</div>

---

## ✨ Features

- **⚡ Blazing Fast Detection:** Pure NumPy vectorized color detection pipeline skips expensive OpenCV conversions, achieving sub-1ms detection times.
- **🖥️ Instant Screen Capture:** Leverages DXGI Desktop Duplication for zero-latency screen grabbing.
- **🛡️ Undetectable Hardware Input:** Communicates entirely via Pure HID Protocol—no COM ports, no standard Serial footprint.
- **🎭 Device Spoofing:** Built-in Razer VID/PID spoofing (`0x1532` / `0x0091`) masks the Arduino hardware.
- **🎯 Dual Modes:** Fully functional precision Aimbot and Triggerbot capabilities.
- **📈 Live Analytics:** Real-time console metrics tracking system latency and frame rates.
- **⚙️ Dynamic Configuration:** Easily adjust colors, FOV, offsets, and sensitivity via an external `settings.json` file.

## 🛠️ Prerequisites

Before you begin, ensure you have met the following requirements:
* **Operating System:** Windows 10 / 11
* **Hardware:** An Arduino board (Leonardo/Micro) flashed with the custom HID firmware (found in `Arduino/`).
* **Python:** Python 3.8 or higher installed on your system.

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Invinciblx777/Colorbot.git
   cd Colorbot
   ```

2. **Install dependencies**
   Install the required Python packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Hardware Setup**
   * Connect your Arduino Leonardo/Micro.
   * Flash the board with the custom HID firmware provided in the `Arduino` directory.
   * Verify the device shows up with spoofed Razer VID/PID credentials.

*(For detailed hardware and environment setup, please refer to [SETUP.md](SETUP.md))*

## 🚀 Usage

To launch the Invinciblx777 engine, run the main script:

```bash
python main.py
```

### Controls (Default)
| Action | Key | Description |
| :--- | :--- | :--- |
| **Toggle Engine** | *Check CLI* | Turns the entire engine ON/OFF |
| **Aimbot** | `Right Click` | Activates aim assist while held down |
| **Triggerbot** | `Left Alt` | Fires weapon automatically when over target |

## ⚙️ Configuration (`settings.json`)

Customize the engine to your exact needs. Key parameters include:
- `capture.fov`: The size of the detection zone around your crosshair.
- `color`: Set the `lower_hue`, `upper_saturation`, etc., to dial in the target color range (HSV format).
- `aimbot.speed`: Adjust tracking sensitivity.
- `aimbot.headshot_offset`: The Y-axis pixel offset for head level targeting.

## ⚠️ Disclaimer

> **Educational Purposes Only**
> This project is designed as an educational proof-of-concept exploring high-performance screen capture, computer vision optimization (NumPy/OpenCV), and hardware abstraction. The authors and contributors are not responsible for any misuse, account bans, or violations of Terms of Service resulting from the use of this software. Use at your own risk.

---

<div align="center">
  <i>Developed by <b>Invinciblx777</b></i>
</div>
