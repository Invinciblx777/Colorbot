/*
  Invinciblx777 Arduino Firmware v2.0
  
  Arduino Leonardo R3 + USB Host Shield 2.0
  
  Features:
  - NO Serial/COM port (CDC disabled)
  - Custom VID/PID: 0x1532/0x0091 (Razer)
  - USB Host Shield passthrough for real mouse
  - HID command channel for Python communication
  - Ping protocol (0xb7) for device discovery
  - Binary move/click commands via HID feature reports
  
  Communication happens via vendor-specific HID feature reports,
  NOT serial. Python uses hidapi to send/receive.
*/

#ifdef dobogusinclude
#include <spi4teensy3.h>
#endif
#include <SPI.h>

#include "hidcustom.h"
#include "CommandChannel.h"

// Movement delta accumulator
signed char delta[3] = {0, 0, 0};

// ============================================================
// USB Host Shield mouse parser — passthrough real mouse input
// ============================================================

void MouseRptParser::Parse(USBHID *hid, bool is_rpt_id, uint8_t len, uint8_t *buf)
{
  MYMOUSEINFO *pmi = (MYMOUSEINFO *)buf;

  // Forward all button state changes
  if (CHECK_BIT(prevState.mouseInfo.buttons, MOUSE_LEFT) != CHECK_BIT(pmi->buttons, MOUSE_LEFT))
  {
    if (CHECK_BIT(pmi->buttons, MOUSE_LEFT))
      Mouse.press(MOUSE_LEFT);
    else
      Mouse.release(MOUSE_LEFT);
  }

  if (CHECK_BIT(prevState.mouseInfo.buttons, MOUSE_RIGHT) != CHECK_BIT(pmi->buttons, MOUSE_RIGHT))
  {
    if (CHECK_BIT(pmi->buttons, MOUSE_RIGHT))
      Mouse.press(MOUSE_RIGHT);
    else
      Mouse.release(MOUSE_RIGHT);
  }

  if (CHECK_BIT(prevState.mouseInfo.buttons, MOUSE_MIDDLE) != CHECK_BIT(pmi->buttons, MOUSE_MIDDLE))
  {
    if (CHECK_BIT(pmi->buttons, MOUSE_MIDDLE))
      Mouse.press(MOUSE_MIDDLE);
    else
      Mouse.release(MOUSE_MIDDLE);
  }

  if (CHECK_BIT(prevState.mouseInfo.buttons, MOUSE_PREV) != CHECK_BIT(pmi->buttons, MOUSE_PREV))
  {
    if (CHECK_BIT(pmi->buttons, MOUSE_PREV))
      Mouse.press(MOUSE_PREV);
    else
      Mouse.release(MOUSE_PREV);
  }

  if (CHECK_BIT(prevState.mouseInfo.buttons, MOUSE_NEXT) != CHECK_BIT(pmi->buttons, MOUSE_NEXT))
  {
    if (CHECK_BIT(pmi->buttons, MOUSE_NEXT))
      Mouse.press(MOUSE_NEXT);
    else
      Mouse.release(MOUSE_NEXT);
  }

  if (pmi->dX || pmi->dY)
    OnMouseMove(pmi);

  if (pmi->wheel)
    OnWheelMove(pmi);

  prevState.bInfo[0] = buf[0];
}

void MouseRptParser::OnMouseMove(MYMOUSEINFO *mi)
{
  delta[0] = mi->dX;
  delta[1] = mi->dY;
}

void MouseRptParser::OnWheelMove(MYMOUSEINFO *mi)
{
  delta[2] = mi->wheel;
}

// ============================================================
// USB Host Shield setup
// ============================================================

#include <usbhub.h>

USB Usb;
USBHub Hub(&Usb);
HIDBoot<USB_HID_PROTOCOL_MOUSE> HidMouse(&Usb);

MouseRptParser Prs;

// ============================================================
// Command processing — handles HID commands from Python
// ============================================================

uint8_t cmdBuffer[CMDCH_REPORT_SIZE];

void processCommand(uint8_t* cmd)
{
  switch (cmd[0])
  {
    case CMD_PING:
    {
      // Respond with ping echo — confirms device is alive
      uint8_t response[CMDCH_REPORT_SIZE] = {0};
      response[0] = CMD_PING;
      CommandChannel.write(response, sizeof(response));
      break;
    }

    case CMD_MOVE:
    {
      // Add software-injected movement to delta
      delta[0] += (int8_t)cmd[1];
      delta[1] += (int8_t)cmd[2];
      break;
    }

    case CMD_CLICK:
    {
      uint8_t btn = cmd[1] ? cmd[1] : MOUSE_LEFT;
      Mouse.click(btn);
      break;
    }

    case CMD_PRESS:
    {
      uint8_t btn = cmd[1] ? cmd[1] : MOUSE_LEFT;
      Mouse.press(btn);
      break;
    }

    case CMD_RELEASE:
    {
      uint8_t btn = cmd[1] ? cmd[1] : MOUSE_LEFT;
      Mouse.release(btn);
      break;
    }
  }
}

// ============================================================
// Setup & Loop
// ============================================================

void setup()
{
  // NO Serial.begin() — CDC is disabled, no COM port exists
  Usb.Init();
  HidMouse.SetReportParser(0, &Prs);
  Mouse.begin();
  CommandChannel.begin();
}

void loop()
{
  // Reset deltas each cycle
  delta[0] = 0;
  delta[1] = 0;
  delta[2] = 0;

  // Poll USB Host Shield (real mouse passthrough)
  Usb.Task();

  // Check for HID commands from Python
  if (CommandChannel.available())
  {
    CommandChannel.read(cmdBuffer, sizeof(cmdBuffer));
    processCommand(cmdBuffer);
  }

  // Apply accumulated movement (real mouse + software injected)
  Mouse.move(delta[0], delta[1], delta[2]);
}