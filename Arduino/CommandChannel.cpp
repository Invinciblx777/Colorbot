/*
  CommandChannel.cpp - Vendor-specific HID interface implementation.
  
  Creates a separate USB HID interface (vendor-specific usage page 0xFF00)
  alongside the mouse HID interface. Python communicates via SET_REPORT /
  GET_REPORT feature reports using hidapi.
  
  IMPORTANT: Windows HidD_SetFeature / HidD_GetFeature include the
  report ID as the first byte of the data phase. We must handle this
  offset when reading/writing feature reports.
*/

#include "CommandChannel.h"

// HID Report Descriptor for vendor-specific command channel
static const uint8_t _cmdChannelHIDDescriptor[] PROGMEM = {
  // Vendor-specific usage page (matches how Razer devices expose config interface)
  0x06, 0x00, 0xFF,           // Usage Page (Vendor Defined 0xFF00)
  0x09, 0x01,                 // Usage (Vendor Usage 1)
  0xA1, 0x01,                 // Collection (Application)
  0x85, CMDCH_REPORT_ID,      //   Report ID (3)
  
  // Feature Report (bidirectional via control endpoint)
  0x09, 0x06,                 //   Usage (Vendor Usage 6)
  0x15, 0x00,                 //   Logical Minimum (0)
  0x26, 0xFF, 0x00,           //   Logical Maximum (255)
  0x75, 0x08,                 //   Report Size (8 bits)
  0x95, CMDCH_REPORT_SIZE,    //   Report Count
  0xB1, 0x02,                 //   Feature (Data, Var, Abs)
  
  // Output Report (host -> device via control SET_REPORT)
  0x09, 0x02,                 //   Usage (Vendor Usage 2)
  0x15, 0x00,                 //   Logical Minimum (0)
  0x26, 0xFF, 0x00,           //   Logical Maximum (255)
  0x75, 0x08,                 //   Report Size (8 bits)
  0x95, CMDCH_REPORT_SIZE,    //   Report Count
  0x91, 0x02,                 //   Output (Data, Var, Abs)
  
  // Input Report (device -> host via interrupt IN)
  0x09, 0x03,                 //   Usage (Vendor Usage 3)
  0x15, 0x00,                 //   Logical Minimum (0)
  0x26, 0xFF, 0x00,           //   Logical Maximum (255)
  0x75, 0x08,                 //   Report Size (8 bits)
  0x95, CMDCH_REPORT_SIZE,    //   Report Count
  0x81, 0x02,                 //   Input (Data, Var, Abs)
  
  0xC0                        // End Collection
};

// Interface descriptor structure matching Arduino core types
typedef struct {
  InterfaceDescriptor  iface;
  HIDDescDescriptor    hidDesc;
  EndpointDescriptor   inEndpoint;
} CommandChannelDescriptor;


CommandChannel_::CommandChannel_(void) : PluggableUSBModule(1, 1, epType) {
  epType[0] = EP_TYPE_INTERRUPT_IN;
  _hasData = false;
  memset(_rxBuffer, 0, sizeof(_rxBuffer));
  memset(_txBuffer, 0, sizeof(_txBuffer));
  memset(_featureBuffer, 0, sizeof(_featureBuffer));
  PluggableUSB().plug(this);
}

void CommandChannel_::begin(void) {
  // Nothing special needed
}

int CommandChannel_::getInterface(uint8_t* interfaceCount) {
  *interfaceCount += 1;
  
  CommandChannelDescriptor desc = {
    D_INTERFACE(pluggedInterface, 1, USB_DEVICE_CLASS_HUMAN_INTERFACE, 
                HID_SUBCLASS_NONE, HID_PROTOCOL_NONE),
    D_HIDREPORT(sizeof(_cmdChannelHIDDescriptor)),
    D_ENDPOINT(USB_ENDPOINT_IN(pluggedEndpoint), USB_ENDPOINT_TYPE_INTERRUPT, 
               USB_EP_SIZE, 0x01)
  };
  
  return USB_SendControl(0, &desc, sizeof(desc));
}

int CommandChannel_::getDescriptor(USBSetup& setup) {
  if (setup.wIndex != pluggedInterface) return 0;
  
  uint8_t descriptorType = (setup.wValueH);
  if (descriptorType == HID_REPORT_DESCRIPTOR_TYPE) {
    return USB_SendControl(TRANSFER_PGM, _cmdChannelHIDDescriptor, 
                           sizeof(_cmdChannelHIDDescriptor));
  }
  return 0;
}

// Helper: extract the command data from a received buffer, skipping report ID if present
static uint8_t* stripReportId(uint8_t* buf, uint16_t &len) {
  // Windows includes the report ID as the first byte of SET_REPORT data phase.
  // If first byte matches our report ID, skip it.
  if (len > 1 && buf[0] == CMDCH_REPORT_ID) {
    len--;
    return buf + 1;
  }
  return buf;
}

bool CommandChannel_::setup(USBSetup& setup) {
  if (setup.wIndex != pluggedInterface) return false;
  
  uint8_t requestType = setup.bmRequestType;
  uint8_t request = setup.bRequest;
  
  // =====================================================
  // GET_REPORT — host reads data from device
  // =====================================================
  if (requestType == REQUEST_DEVICETOHOST_CLASS_INTERFACE) {
    if (request == HID_GET_REPORT) {
      uint8_t reportType = setup.wValueH;
      
      if (reportType == 3) { // Feature report
        // Windows expects: [report_id, data...]
        // Prepend report ID to the response
        uint8_t response[CMDCH_REPORT_SIZE + 1];
        response[0] = CMDCH_REPORT_ID;
        memcpy(&response[1], _featureBuffer, CMDCH_REPORT_SIZE);
        return USB_SendControl(0, response, sizeof(response)) > 0;
      }
      if (reportType == 1) { // Input report
        uint8_t response[CMDCH_REPORT_SIZE + 1];
        response[0] = CMDCH_REPORT_ID;
        memcpy(&response[1], _txBuffer, CMDCH_REPORT_SIZE);
        return USB_SendControl(0, response, sizeof(response)) > 0;
      }
    }
  }
  
  // =====================================================
  // SET_REPORT — host sends data to device
  // =====================================================
  if (requestType == REQUEST_HOSTTODEVICE_CLASS_INTERFACE) {
    if (request == HID_SET_REPORT) {
      uint8_t reportType = setup.wValueH;
      uint16_t length = setup.wLength;
      
      // Temporary buffer to receive raw data (may include report ID)
      uint8_t rawBuf[CMDCH_REPORT_SIZE + 2];
      if (length > sizeof(rawBuf)) length = sizeof(rawBuf);
      
      if (reportType == 3 || reportType == 2) { // Feature or Output report
        // Read ALL bytes from the control endpoint
        USB_RecvControl(rawBuf, length);
        
        // Strip the report ID byte if present (Windows includes it)
        uint16_t dataLen = length;
        uint8_t* cmdData = stripReportId(rawBuf, dataLen);
        
        // Copy clean command data (without report ID) into rxBuffer
        uint8_t copyLen = (dataLen < CMDCH_REPORT_SIZE) ? dataLen : CMDCH_REPORT_SIZE;
        memcpy(_rxBuffer, cmdData, copyLen);
        _hasData = true;
        
        // If it's a ping, immediately prepare the response
        if (_rxBuffer[0] == CMD_PING) {
          memset(_featureBuffer, 0, sizeof(_featureBuffer));
          _featureBuffer[0] = CMD_PING; // Echo ping back
        }
        return true;
      }
    }
  }
  
  return false;
}

bool CommandChannel_::available(void) {
  return _hasData;
}

uint8_t CommandChannel_::read(uint8_t* buffer, uint8_t maxLen) {
  if (!_hasData) return 0;
  
  uint8_t len = (maxLen < CMDCH_REPORT_SIZE) ? maxLen : CMDCH_REPORT_SIZE;
  memcpy(buffer, _rxBuffer, len);
  _hasData = false;
  return len;
}

void CommandChannel_::write(const uint8_t* buffer, uint8_t len) {
  if (len > CMDCH_REPORT_SIZE) len = CMDCH_REPORT_SIZE;
  memcpy(_txBuffer, buffer, len);
  memcpy(_featureBuffer, buffer, len);
  
  // Also send as interrupt IN report (prepend report ID)
  uint8_t report[CMDCH_REPORT_SIZE + 1];
  report[0] = CMDCH_REPORT_ID;
  memcpy(&report[1], buffer, len);
  USB_Send(pluggedEndpoint | TRANSFER_RELEASE, report, len + 1);
}

CommandChannel_ CommandChannel;
