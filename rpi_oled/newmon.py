#!/usr/bin/env python3
## monitor_ssd1306_supervisor.py
# System status monitor querying Home Assistant states via the Supervisor API proxy for an SSD1306

import os
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306


class HASupervisorSystemMonitor:
    #: __init__
    #  Initialises the SSD1306 display on /dev/i2c-1 at 0x3C and sets up API headers
    def __init__(self, bus_number=1, address=0x3C):
        self.bus_number = bus_number
        self.address = address
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
        #  Token automatically provided by HA Supervisor inside the Add-on container
        self.supervisor_token = os.environ.get("SUPERVISOR_TOKEN", "")
        #= headers
        self.headers = {
            "Authorization": f"Bearer {self.supervisor_token}",
            "Content-Type": "application/json",
        }

    #: get_state_value
    #  Extracts state string from HA Core API via the Supervisor proxy
    def get_state_value(self, entity_id):
        if not self.supervisor_token:
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
    #  Retrieves system host name from HA Core config endpoint or fallback
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

    #: get_cpu_info
    #  Retrieves CPU temp and utilisation states via API
    def get_cpu_info(self):
        temp_val = self.get_state_value("sensor.processor_temperature")
        usage_val = self.get_state_value("sensor.processor_use")

        try:
            temp = float(temp_val) if temp_val else 0.0
        except ValueError:
            temp = 0.0

        try:
            usage = float(usage_val) if usage_val else 0.0
        except ValueError:
            usage = 0.0

        return temp, usage

    #: get_memory_info
    #  Retrieves RAM usage and total memory formatted to nearest GiB
    def get_memory_info(self):
        used_val = self.get_state_value("sensor.memory_use")
        free_val = self.get_state_value("sensor.memory_free")

        try:
            used_mib = float(used_val)
            free_mib = float(free_val)
            total_gib = round((used_mib + free_mib) / 1024)
            used_gib = round(used_mib / 1024)
            return f"{used_gib}/{total_gib}GiB"
        except (ValueError, TypeError):
            return "N/AGiB"

    #: get_storage_info
    #  Retrieves disk usage states formatted to GiB or TiB
    def get_storage_info(self):
        used_val = self.get_state_value("sensor.disk_use_")
        free_val = self.get_state_value("sensor.disk_free_")

        try:
            used_gib = float(used_val) if used_val else 0.0
            free_gib = float(free_val) if free_val else 0.0
            total_gib = used_gib + free_gib

            if total_gib >= 1000:
                total_str = f"{round(total_gib / 1024)}TiB"
            else:
                total_str = f"{round(total_gib)}GiB"

            if used_gib >= 1000:
                used_str = f"{round(used_gib / 1024)}TiB"
            else:
                used_str = f"{round(used_gib)}GiB"

            return f"{used_str}/{total_str}"
        except (ValueError, TypeError):
            return "N/A"

    #: get_network_info
    #  Retrieves throughput speeds converted from MB/s to Mb/s
    def get_network_info(self):
        tx_val = self.get_state_value("sensor.network_throughput_out_eth0")
        rx_val = self.get_state_value("sensor.network_throughput_in_eth0")

        if tx_val is None:
            tx_val = self.get_state_value("sensor.network_throughput_out")
            rx_val = self.get_state_value("sensor.network_throughput_in")

        try:
            ul_mbps = float(tx_val) * 8.0 if tx_val else 0.0
            dl_mbps = float(rx_val) * 8.0 if rx_val else 0.0
            return ul_mbps, dl_mbps
        except (ValueError, TypeError):
            return 0.0, 0.0

    #: update_display
    #  Renders state engine snapshot to SSD1306
    def update_display(self):
        if not self.device:
            return

        hostname = self.get_hostname()
        temp, cpu_pct = self.get_cpu_info()
        ram_str = self.get_memory_info()
        root_str = self.get_storage_info()
        ul_speed, dl_speed = self.get_network_info()

        with canvas(self.device) as draw:
            # Header bar with inverse white background
            draw.rectangle((0, 0, 127, 11), fill="white")
            draw.text((2, 0), hostname, fill="black")

            # Row 1: CPU Temp | CPU Usage
            draw.text((0, 15), f"CPU: {temp:.1f}\u00b0C | {cpu_pct:.0f}%", fill="white")

            # Row 2: RAM Usage / Total
            draw.text((0, 27), f"RAM: {ram_str}", fill="white")

            # Row 3: Root Drive Usage / Total
            draw.text((0, 39), f"DISK: {root_str}", fill="white")

            # Row 4: Network Speeds (Uplink | Download)
            draw.text((0, 51), f"NET: {ul_speed:.1f}M \u2191 | {dl_speed:.1f}M \u2193", fill="white")

    #: run
    #  Main execution loop for standalone add-on execution
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
    monitor = HASupervisorSystemMonitor(bus_number=1, address=0x3C)
    monitor.run()