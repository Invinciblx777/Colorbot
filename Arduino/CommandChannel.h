/*
  CommandChannel.h - Vendor-specific HID interface for receiving
  commands from the host (Python) without using Serial/CDC.
  
  This creates a second HID interface with a vendor-specific usage page.
  Python communicates via hidapi using feature reports.
  
  Protocol:
    0xb7 = Ping (Arduino echoes 0xb7 back)
    0x01 = Move (x, y as signed bytes)
    0x02 = Click (button mask)
    0x03 = Press (button mask)
    0x04 = Release (button mask)
*/

#pragma once

#include <Arduino.h>
#include "PluggableUSB.h"
#include <HID.h>

// Command bytes
#define CMD_PING    0xb7
#define CMD_MOVE    0x01
#define CMD_CLICK   0x02
#define CMD_PRESS   0x03
#define CMD_RELEASE 0x04

// Report config
#define CMDCH_REPORT_SIZE 8
#define CMDCH_REPORT_ID   0x03

class CommandChannel_ : public PluggableUSBModule {
public:
  CommandChannel_(void);
  void begin(void);
  
  // Check if a command has been received
  bool available(void);
  
  // Read the last received command into buffer (returns bytes read)
  uint8_t read(uint8_t* buffer, uint8_t maxLen);
  
  // Send a response back to the host
  void write(const uint8_t* buffer, uint8_t len);

protected:
  // PluggableUSB interface
  int getInterface(uint8_t* interfaceCount);
  int getDescriptor(USBSetup& setup);
  bool setup(USBSetup& setup);
  
private:
  uint8_t epType[1];
  volatile bool _hasData;
  uint8_t _rxBuffer[CMDCH_REPORT_SIZE];
  uint8_t _txBuffer[CMDCH_REPORT_SIZE];
  uint8_t _featureBuffer[CMDCH_REPORT_SIZE];
};

extern CommandChannel_ CommandChannel;
