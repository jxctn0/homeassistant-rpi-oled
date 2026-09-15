#!/usr/bin/env python3
## monitor_ssd1306_supervisor.py
# System status monitor rendering 12x12 icons and 5x7px formatted text to SSD1306

import json
import os
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

#= OPTIONS_PATH
OPTIONS_PATH = "/data/options.json"
#= ICONS_DIR
ICONS_DIR = "/app/icons"

# Default configuration fallback
DEFAULT_CONFIG = {
    "bus_number": 1,
    "i2c_address": "0x3C",
    "sensor_cpu_arch": "sensor.processor_architecture",
    "sensor_cpu_temp": "sensor.processor_temperature",
    "sensor_cpu_use": "sensor.processor_use",
    "sensor_ram_use": "sensor.memory_use",
    "sensor_ram_free": "sensor.memory_free",
    "sensor_disk_use": "sensor.disk_use_",
    "sensor_disk_free": "sensor.disk_free_",
    "sensor_net_tx": "sensor.network_throughput_out_eth0",
    "sensor_net_rx": "sensor.network_throughput_in_eth0",
    "sensor_net_type": "sensor.network_interface_type",
}


class HASupervisorSystemMonitor:
    #: __init__
    #  Loads configuration, pre-loads 12x12 icons, sets 5x7 bitmap font, and initialises OLED
    def __init__(self):
        self.config = self.load_config()

        # Parse I2C address string
        try:
            addr_str = self.config.get("i2c_address", "0x3C")
            self.address = int(addr_str, 16) if isinstance(addr_str, str) else int(addr_str)
        except ValueError:
            self.address = 0x3C

        self.bus_number = int(self.config.get("bus_number", 1))
        self.device = None

        try:
            serial = i2c(port=self.bus_number, address=self.address)
            self.device = ssd1306(serial, width=128, height=64)
            print(
                f"Initialised SSD1306 on /dev/i2c-{self.bus_number} at {hex(self.address)}"
            )
        except Exception as e:
            print(f"Failed to initialise display: {e}")
            self.device = None

        #= supervisor_token
        self.supervisor_token = os.environ.get("SUPERVISOR_TOKEN", "")
        #= headers
        self.headers = {
            "Authorization": f"Bearer {self.supervisor_token}",
            "Content-Type": "application/json",
        }

        # Load 5x7 default pixel font
        self.font = ImageFont.load_default()

        # Pre-load 12x12 icon images
        self.icons = self.load_icons()

    #: load_icons
    #  Pre-loads 12x12 1-bit monochrome images from /app/icons/
    def load_icons(self):
        icon_names = [
            "cpu_32",
            "cpu_64",
            "cpu_temp",
            "cpu_usage",
            "memory",
            "disk",
            "wifi",
            "ethernet",
            "net_up",
            "net_down",
            "ha",
        ]
        loaded_icons = {}

        for name in icon_names:
            for ext in ["png", "bmp", "pbm"]:
                icon_path = os.path.join(ICONS_DIR, f"{name}.{ext}")
                if os.path.exists(icon_path):
                    try:
                        img = Image.open(icon_path).convert("1")
                        # Resize to exact 12x12 dimensions if needed
                        if img.size != (12, 12):
                            img = img.resize((12, 12))
                        loaded_icons[name] = img
                        print(f"Loaded icon: {icon_path}")
                        break
                    except Exception as e:
                        print(f"Failed to load icon {icon_path}: {e}")
            if name not in loaded_icons:
                loaded_icons[name] = None

        return loaded_icons

    #: load_config
    def load_config(self):
        if os.path.exists(OPTIONS_PATH):
            try:
                with open(OPTIONS_PATH, "r") as f:
                    user_opts = json.load(f)
                    return {**DEFAULT_CONFIG, **user_opts}
            except Exception as e:
                print(f"Failed to read options file: {e}")
        return DEFAULT_CONFIG

    #: get_state_value
    def get_state_value(self, entity_id):
        if not self.supervisor_token or not entity_id:
            return None
        try:
            url = f"http://supervisor/core/api/states/{entity_id}"
            response = requests.get(url, headers=self.headers, timeout=3)
            if response.status_code == 200:
                state_val = response.json().get("state")
                if state_val not in ("unavailable", "unknown"):
                    return state_val
            return None
        except Exception:
            return None

    #: get_hostname
    def get_hostname(self):
        if not self.supervisor_token:
            return "HOMEASSISTANT"
        try:
            url = "http://supervisor/core/api/config"
            response = requests.get(url, headers=self.headers, timeout=3)
            if response.status_code == 200:
                name = response.json().get("location_name")
                return name.upper() if name else "HOMEASSISTANT"
            return "HOMEASSISTANT"
        except Exception:
            return "HOMEASSISTANT"

    #: format_bytes_rate
    #  Converts raw MB/s or Bytes/s throughput value to formatted nn.nn + unit string
    def format_bytes_rate(self, raw_val):
        try:
            # Assume state is reported in MB/s by default System Monitor
            val = float(raw_val) * 1024 * 1024
        except (ValueError, TypeError):
            return "00.00", "B"

        if val >= 1024**3:
            return f"{val / (1024**3):05.2f}", "GB"
        elif val >= 1024**2:
            return f"{val / (1024**2):05.2f}", "MB"
        elif val >= 1024:
            return f"{val / 1024:05.2f}", "KB"
        else:
            return f"{val:05.2f}", "B"

    #: draw_icon
    #  Helper function to safely paste a 12x12 icon image at (x, y)
    def draw_icon(self, draw, x, y, icon_key, fill_color="white"):
        icon = self.icons.get(icon_key)
        if icon:
            draw.bitmap((x, y), icon, fill=fill_color)
            return x + 13
        return x

    #: update_display
    #  Renders state engine snapshot based on exact formatting layout
    def update_display(self):
        if not self.device:
            return

        hostname = self.get_hostname()

        # Fetch CPU info
        cpu_arch_val = self.get_state_value(self.config.get("sensor_cpu_arch"))
        is_64bit = "64" in str(cpu_arch_val) if cpu_arch_val else True
        cpu_icon_key = "cpu_64" if is_64bit else "cpu_32"

        try:
            raw_temp = float(self.get_state_value(self.config.get("sensor_cpu_temp")) or 0.0)
            cpu_temp_str = f"{round(raw_temp):>3d}"
        except ValueError:
            cpu_temp_str = "  0"

        try:
            raw_use = float(self.get_state_value(self.config.get("sensor_cpu_use")) or 0.0)
            cpu_usage_str = f"{round(raw_use):>3d}"
        except ValueError:
            cpu_usage_str = "  0"

        # Fetch Memory info
        try:
            ram_used_mib = float(self.get_state_value(self.config.get("sensor_ram_use")) or 0.0)
            ram_free_mib = float(self.get_state_value(self.config.get("sensor_ram_free")) or 0.0)
            total_mib = ram_used_mib + ram_free_mib
            mem_used_gb = round(ram_used_mib / 1024)
            mem_total_gb = round(total_mib / 1024)
            mem_pct = round((ram_used_mib / total_mib) * 100) if total_mib > 0 else 0
        except (ValueError, TypeError):
            mem_used_gb, mem_total_gb, mem_pct = 0, 0, 0

        # Fetch Disk info
        try:
            disk_used_gb = round(float(self.get_state_value(self.config.get("sensor_disk_use")) or 0.0))
            disk_free_gb = float(self.get_state_value(self.config.get("sensor_disk_free")) or 0.0)
            disk_total_gb = round(disk_used_gb + disk_free_gb)
        except (ValueError, TypeError):
            disk_used_gb, disk_total_gb = 0, 0

        # Fetch Network info
        net_type = self.get_state_value(self.config.get("sensor_net_type"))
        net_icon_key = "wifi" if net_type and "wifi" in str(net_type).lower() else "ethernet"

        raw_tx = self.get_state_value(self.config.get("sensor_net_tx"))
        raw_rx = self.get_state_value(self.config.get("sensor_net_rx"))
        tx_val_str, tx_unit = self.format_bytes_rate(raw_tx)
        rx_val_str, rx_unit = self.format_bytes_rate(raw_rx)

        with canvas(self.device) as draw:
            # Row 0: Inverted Header Bar (Hostname + optional HA icon)
            draw.rectangle((0, 0, 127, 12), fill="white")
            x_pos = self.draw_icon(draw, 1, 0, "ha", fill_color="black")
            draw.text((x_pos, 2), hostname, font=self.font, fill="black")

            # Row 1: <cpu> <cpu_temp> {temp}°C <cpu_usage> {usage}%
            y_row1 = 15
            x_pos = self.draw_icon(draw, 0, y_row1, cpu_icon_key)
            x_pos = self.draw_icon(draw, x_pos, y_row1, "cpu_temp")
            draw.text((x_pos, y_row1 + 2), f"{cpu_temp_str}\u00b0C", font=self.font, fill="white")
            
            x_pos += 26
            x_pos = self.draw_icon(draw, x_pos, y_row1, "cpu_usage")
            draw.text((x_pos, y_row1 + 2), f"{cpu_usage_str}%", font=self.font, fill="white")

            # Row 2: <memory> {memory_used}GB / {memory_total}GB ({memused_percentage}%)
            y_row2 = 28
            x_pos = self.draw_icon(draw, 0, y_row2, "memory")
            draw.text(
                (x_pos, y_row2 + 2),
                f"{mem_used_gb}GB / {mem_total_gb}GB ({mem_pct}%)",
                font=self.font,
                fill="white",
            )

            # Row 3: <disk> {disk_usage} GB / {disk_total} GB
            y_row3 = 40
            x_pos = self.draw_icon(draw, 0, y_row3, "disk")
            draw.text(
                (x_pos, y_row3 + 2),
                f"{disk_used_gb} GB / {disk_total_gb} GB",
                font=self.font,
                fill="white",
            )

            # Row 4: <network_icon> {net_tx}{unit}<net_up> {net_rx}{unit}<net_down>
            y_row4 = 52
            x_pos = self.draw_icon(draw, 0, y_row4, net_icon_key)
            draw.text((x_pos, y_row4 + 2), f"{tx_val_str}{tx_unit}", font=self.font, fill="white")
            x_pos += 38
            
            x_pos = self.draw_icon(draw, x_pos, y_row4, "net_up")
            draw.text((x_pos, y_row4 + 2), f"{rx_val_str}{rx_unit}", font=self.font, fill="white")
            x_pos += 38
            self.draw_icon(draw, x_pos, y_row4, "net_down")

    #: run
    def run(self):
        if not self.device:
            print("No display available. Exiting.")
            return

        while True:
            try:
                self.update_display()
                time.sleep(2)
            except Exception as e:
                print(f"Runtime error: {e}")
                time.sleep(5)


if __name__ == "__main__":
    monitor = HASupervisorSystemMonitor()
    monitor.run()