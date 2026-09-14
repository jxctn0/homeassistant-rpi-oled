# rpi OLED Monitor - Documentation

## Description

This add-on displays real-time system information on an i2c OLED display connected to your Raspberry Pi running Home Assistant.

## Displayed Information

- **CPU:** Percentage usage and current frequency
- **RAM:** Usage and total available
- **Temperature:** Processor temperature
- **Storage:** Available disk space
- **Network:** Local IP address
    > **TODO:** Adding support for any Home Assistant Entity, configuarble through the UI

## Mandatory Prerequisites

### 1. Hardware

- Raspberry Pi (4) running Home Assistant OS
- Compatible i2c OLED display (SSD1306 with 128x64px)
- Display correctly connected to the Raspberry Pi's i2c pins

### 2. Enabling i2c

> **IMPORTANT:** Before installing this add-on, **you must enable i2c** on your system.

#### Procedure to enable i2c:

1. Go to **Supervisor → Add-on Store → Menu (⋮) → Repositories**
2. Add this repository: `https://github.com/Poeschl/Hassio-Addons`
3. Search for and install **"HassOS i2c Configurator"**
4. Start the add-on
5. **CRITICAL:** Perform a **full shutdown** (not just a restart):

- Go to **Settings → System → Shut Down**
- Physically disconnect the power supply for 10 seconds
- Reconnect and let it reboot
- **Repeat this process a second time** (required to apply the changes)

6. Verify that i2c is active by connecting via SSH: `ls -l /dev/i2c-*`

If you see devices that match `/dev/i2c-0`, i2c is correctly enabled!
if you don't, make sure you have followed the Enabling i2c instructions, and you are using
this repository, (jxctn0/homeassistant-rpi-oled)[https://github.com/jxctn0/homeassistant-rpi-oled] - (davidelolli/homeassistant-rpi5-oled)[https://github.com/davidelolli/homeassistant-rpi5-oled] ONLY supports the Pi 5.

## Installation

1. Add this repository to Home Assistant:

- **Supervisor → Add-on Store → Menu (⋮) → Repositories**
- Paste: `https://github.com/jxctn0/homeassistant-rpi-oled`
- Click "Add"

2. Search for **"RPi OLED Monitor"** in the add-on list

3. Click **"Install"**

4. Wait for the installation to complete

5. Click **"Start"**

## Configuration

The Pi4 has 7 user-accessible i2c busses (not including HDMI-EDID ones... but lets not worry about that here ;) ).
On my personal RPi I use pins 2 and 3 for `SDA` and `SCL` respectively. You can choose whichever, but make sure to set the right bus in the config you are on.
A good resource to use is (this)[https://pinout.xyz/pinout/i2c#I2C%20-%20Inter%20Integrated%20Circuit] guide to raspberry pi pinouts, and sourced from that site is this table, to show what busses correspond to which pins:

| Pins                | Pi 4         | Pi 5 | Notes                              |
| ------------------- | ------------ | ---- | ---------------------------------- |
| GPIO 0 and GPIO 1   | i2c0 or i2c6 | i2c0 | Usually left alone for HAT EEPROMs |
| GPIO 2 and GPIO 3   | i2c1 or i2c3 | i2c1 |                                    |
| GPIO 4 and GPIO 5   | i2c3         | i2c2 |                                    |
| GPIO 6 and GPIO 7   | i2c4         | i2c3 |                                    |
| GPIO 8 and GPIO 9   | i2c4         | i2c0 |                                    |
| GPIO 10 and GPIO 11 | i2c5         | i2c1 |                                    |
| GPIO 12 and GPIO 13 | i2c5         | i2c2 |                                    |
| GPIO 14 and GPIO 15 | i2c3         |      | Also the UART pins                 |
| GPIO 22 and GPIO 23 | i2c6         | i2c3 |                                    |

## Automatic Startup

To have the add-on start automatically when Home Assistant boots up:

- On the add-on page, enable the **"Start on boot"** option

## Troubleshooting

### The display remains off

**Cause:** i2c is not enabled or the display is not connected correctly.

**Solution:**

1. Check the physical connection of the display (SDA and SCL are on the same bus (i.e. neighbouring pins), youre using the correct poer rail for your display (most i2c devices use the 3.3v pin), and you're using a valid ground pin)
2. Verify that i2c is active: `ls /dev/i2c-*` - this should show at lest _some_ i2c devices created for HDMI-EDID, if not the right one
3. Check the logs. I've implemented `i2cdetect` to scan each valid bus, your display _should_ be in this. if not, your display may be faulty, or it may be connected incorrectly.

### Installation error

**Cause:** Issue with the Docker build.

**Solution:**

1. Check your internet connection
2. Retry the installation
3. Check the add-on logs for specific details

### Display shows incorrect information

**Cause:** Outdated Python script or i2c communication issue. **Solution:**

1. Restart the add-on
2. Verify that the display is working correctly using `i2cdetect`

## Support

To report issues or request features, open an issue at:
`https://github.com/jxctn0/homeassistant-rpi-oled/issues`

## Credits

Add-on initialy developed by Davide Lolli
Added support for Pi4 by Jace Cotugno
