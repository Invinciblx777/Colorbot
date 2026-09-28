# Invinciblx777 v2.0 — Arduino Setup Guide

## Prerequisites
- Arduino IDE installed
- Arduino Leonardo R3
- USB Host Shield 2.0
- USB Host Shield 2.0 library installed in Arduino IDE
  (Sketch → Include Library → Manage Libraries → search "USB Host Shield Library 2.0")

---

## Step 1: Modify boards.txt (Custom VID/PID + Disable CDC)

### Find boards.txt
The file is located at:
```
C:\Users\<YourUsername>\AppData\Local\Arduino15\packages\arduino\hardware\avr\<version>\boards.txt
```
Or if using the classic Arduino IDE:
```
C:\Program Files (x86)\Arduino\hardware\arduino\avr\boards.txt
```

### Add Custom Board Entry

Open `boards.txt` in a text editor (run as Administrator) and add this at the **end** of the file:

```properties
##############################################################
# Invinciblx777 — Leonardo with Razer VID/PID, CDC Disabled
##############################################################

invinciblx777.name=Invinciblx777 (Leonardo HID-Only)
invinciblx777.vid.0=0x1532
invinciblx777.pid.0=0x0091
invinciblx777.vid.1=0x1532
invinciblx777.pid.1=0x0091

invinciblx777.upload.tool=avrdude
invinciblx777.upload.protocol=avr109
invinciblx777.upload.maximum_size=28672
invinciblx777.upload.maximum_data_size=2560
invinciblx777.upload.speed=57600
invinciblx777.upload.disable_flushing=true
invinciblx777.upload.use_1200bps_touch=true
invinciblx777.upload.wait_for_upload_port=true

invinciblx777.bootloader.tool=avrdude
invinciblx777.bootloader.low_fuses=0xff
invinciblx777.bootloader.high_fuses=0xd8
invinciblx777.bootloader.extended_fuses=0xcb
invinciblx777.bootloader.file=caterina/Caterina-Leonardo.hex
invinciblx777.bootloader.unlock_bits=0x3F
invinciblx777.bootloader.lock_bits=0x2F

invinciblx777.build.mcu=atmega32u4
invinciblx777.build.f_cpu=16000000L
invinciblx777.build.vid=0x1532
invinciblx777.build.pid=0x0091
invinciblx777.build.usb_product="Razer Viper"
invinciblx777.build.usb_manufacturer="Razer"
invinciblx777.build.board=AVR_LEONARDO
invinciblx777.build.core=arduino
invinciblx777.build.variant=leonardo
invinciblx777.build.extra_flags={build.usb_flags} -DCDC_DISABLED
```

### Save and restart Arduino IDE.

---

## Step 2: Disable CDC in Arduino Core

### Find USBDesc.h
```
C:\Users\<YourUsername>\AppData\Local\Arduino15\packages\arduino\hardware\avr\<version>\cores\arduino\USBDesc.h
```

### Modify USBDesc.h

Find this line:
```cpp
#define CDC_ENABLED
```

Replace it with:
```cpp
#ifndef CDC_DISABLED
#define CDC_ENABLED
#endif
```

This makes CDC conditional — when we build with `-DCDC_DISABLED` (set in our custom board entry), the COM port won't be created.

### Save the file.

---

## Step 3: Flash the Arduino

1. Open Arduino IDE
2. Open the `Arduino/Arduino.ino` sketch from this project
3. Go to **Tools → Board** and select **"Invinciblx777 (Leonardo HID-Only)"**
4. Go to **Tools → Port** and select the Leonardo's current COM port
5. Click **Upload**

### ⚠️ IMPORTANT: After Flashing
Once flashed, the Arduino will **NO LONGER show a COM port**. 
This is by design — it's now a pure HID device.

### How to Re-flash (if needed)
Since there's no COM port, you need to use the bootloader:

1. **Double-tap the RESET button** on the Leonardo quickly
2. The bootloader will briefly show a COM port for ~8 seconds
3. **Immediately** select that port in Arduino IDE (Tools → Port)
4. Click Upload **within those 8 seconds**

Tip: Start the upload first, then double-tap reset when it says "Uploading..."

---

## Step 4: Verify

After flashing:
1. Open **Device Manager** (Win+X → Device Manager)
2. Under **Human Interface Devices**, you should see the device
3. There should be **NO COM port** under "Ports (COM & LPT)" for this device
4. The device should identify as **"Razer Viper"** with VID 0x1532 / PID 0x0091

---

## Step 5: Python Setup

```bash
pip install -r requirements.txt
```

Then run:
```bash
python main.py
```

The Python script will:
1. Find the device by VID/PID (0x1532/0x0091)
2. Send ping (0xb7) to verify connection
3. Start the color detection engine

---

## Troubleshooting

### "No HID device found"
- Make sure the Arduino is plugged in
- Check Device Manager for the device
- Try unplugging and replugging
- Double-tap RESET and re-flash

### "Ping failed"
- The device was found but isn't responding to commands
- Make sure you flashed the correct firmware
- Check that the USB Host Shield is properly seated

### Can't upload new firmware
- Double-tap RESET quickly to enter bootloader mode
- Select the temporary COM port that appears
- Upload within 8 seconds

### d3dshot import error
- d3dshot requires Windows 10+ and DirectX 11
- The code will automatically fall back to mss if d3dshot isn't available
- You can safely ignore this if mss works fine for you
