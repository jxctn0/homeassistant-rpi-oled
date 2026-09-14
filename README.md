# 🖥️ rpi OLED Monitor - Home Assistant Add-on

[![Home Assistant][ha-shield]][ha-url]
[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

Display system information on an i2c OLED screen connected to your Raspberry Pi 5 running Home Assistant OS.

<img width="1376" height="768" alt="hf_20260217_220523_3726a7e3-6c1d-4beb-83b3-325dfc94506c" src="https://github.com/user-attachments/assets/068de92b-8591-407e-a66d-5130d1a50ed4" />

## !! NOTE !!

This repository is a fork of [`jxctn0/homeassistant-rpi-oled`](https://github.com/jxctn0/homeassistant-rpi-oled) - I am just updating it to add functionality for other Raspberry Pis (i.e. RPi 4 at first. may end up with others, but this is NO promise)

## ✨ Features

- 📊 Real-time CPU usage and frequency monitoring
- 💾 RAM usage statistics
- 🌡️ System temperature monitoring
- 💽 Storage space tracking
- 🌐 Network IP address display
- 🔄 Auto-refresh every few seconds

## 📋 Requirements

- Raspberry Pi with Home Assistant OS
- i2c OLED Display
- i2c enabled on your system

## 🚀 Installation

### Step 1: Enable i2c

**This is mandatory before installing the addon!**

1. Go to **Supervisor → Add-on Store → Menu (⋮) → Repositories**
2. Add repository: `https://github.com/Poeschl/Hassio-Addons`
3. Install and start **"HassOS i2c Configurator"**
4. **Perform a complete shutdown twice** (unplug power physically)
5. Verify i2c is active: `ls /dev/i2c-*`

### Step 2: Install the Add-on

1. Go to **Supervisor → Add-on Store → Menu (⋮) → Repositories**
2. Add this repository:
   `https://github.com/jxctn0/homeassistant-rpi-oled`
3. Find **"RPi OLED Monitor"** in the add-on list
4. Click **"Install"**
5. Click **"Start"**

## 📖 Documentation

For detailed documentation, troubleshooting, and configuration options, see [DOCS.md](rpi_oled/DOCS.md).

## 🐛 Bug Reports & Feature Requests

Found a bug or have a feature request? Please open an [issue](https://github.com/jxctn0/homeassistant-rpi-oled/issues).

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 👨‍💻 Author

Developed by **Davide Lolli** for the Home Assistant community.

---

**⭐ If this add-on helps you, consider giving it a star on GitHub!**

[ha-shield]: https://img.shields.io/badge/Home%20Assistant-Add--on-blue.svg
[ha-url]: https://www.home-assistant.io/
[releases-shield]: https://img.shields.io/github/v/release/jxctn0/homeassistant-rpi-oled
[releases]: https://github.com/TUO_USERNAME/homeassistant-rpi-oled/releases
[license-shield]: https://img.shields.io/github/license/jxctn0/homeassistant-rpi-oled
