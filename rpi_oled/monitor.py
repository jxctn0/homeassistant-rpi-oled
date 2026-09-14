#!/usr/bin/env python3
## monitor_ssd1306.py
# System status monitor drawing natively to an SSD1306 OLED on /dev/i2c-1

import os
import subprocess
import time
from pathlib import Path
import psutil
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306


class RPiSystemMonitor:
    #: __init__
    #  Initialises the SSD1306 display on /dev/i2c-1 at 0x3C
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

        self.last_nvme_check_time = 0
        self.nvme_error_status = False

    #: get_cpu_usage
    def get_cpu_usage(self):
        return psutil.cpu_percent(interval=1)

    #: get_memory_info
    def get_memory_info(self):
        mem = psutil.virtual_memory()
        total_gb = round(mem.total / (1024**3), 1)
        return mem.percent, total_gb

    #: get_temperature
    def get_temperature(self):
        try:
            zones = [
                "/sys/class/thermal/thermal_zone0/temp",
                "/sys/class/thermal/thermal_zone1/temp",
            ]
            for zone in zones:
                if os.path.exists(zone):
                    with open(zone, "r") as f:
                        return float(f.read().strip()) / 1000.0
            return 0.0
        except Exception:
            return 0.0

    #: get_nvme_size
    def get_nvme_size(self):
        try:
            if not os.path.exists("/dev/nvme0n1"):
                return None
            with open("/sys/block/nvme0n1/size", "r") as f:
                sectors = int(f.read().strip())
                return round((sectors * 512) / (1024**3), 1)
        except Exception:
            return None

    #: get_root_device
    def get_root_device(self):
        try:
            with open("/proc/mounts", "r") as f:
                for line in f:
                    device, mount_point, *_ = line.split()
                    if mount_point == "/":
                        return device
            return None
        except Exception:
            return None

    #: get_storage_info
    def get_storage_info(self):
        try:
            root_disk = psutil.disk_usage("/")
            root_total_gb = round(root_disk.total / (1024**3), 1)
            root_used_percent = root_disk.percent
            root_device = self.get_root_device()
            is_root_nvme = (
                root_device is not None and "nvme" in root_device.lower()
            )
            nvme_size = self.get_nvme_size()
            nvme_info = (True, nvme_size) if nvme_size is not None else None

            return {
                "is_root_nvme": is_root_nvme,
                "root_used_percent": root_used_percent,
                "root_total_gb": root_total_gb,
                "nvme_info": nvme_info,
            }
        except Exception:
            return None

    #: draw_progress_bar
    #  Draws an outlined progress bar on the Pillow canvas
    def draw_progress_bar(self, draw, x, y, width, height, percent):
        # Outline
        draw.rectangle((x, y, x + width, y + height), outline="white", fill="black")
        # Fill ratio
        fill_width = int((width - 2) * (max(0, min(100, percent)) / 100.0))
        if fill_width > 0:
            draw.rectangle(
                (x + 1, y + 1, x + 1 + fill_width, y + height - 1),
                outline="white",
                fill="white",
            )

    #: run
    #  Cycling display loop (CPU/MEM -> Storage -> Temp -> Clock)
    def run(self):
        if not self.device:
            print("No display available. Exiting.")
            return

        display_cycle = 0
        cycle_start_time = time.time()

        while True:
            try:
                current_time = time.time()
                cycle_duration = 8 if display_cycle < 2 else 5

                if current_time - cycle_start_time >= cycle_duration:
                    cycle_start_time = current_time
                    display_cycle = (display_cycle + 1) % 4

                with canvas(self.device) as draw:
                    # Header bar across top
                    draw.rectangle((0, 0, 127, 10), fill="white")
                    draw.text((2, 0), "SYS MONITOR", fill="black")

                    # Page 0: CPU & RAM Usage + Progress Bars
                    if display_cycle == 0:
                        cpu = self.get_cpu_usage()
                        mem_pct, mem_total = self.get_memory_info()

                        draw.text((0, 14), f"CPU: {cpu:.1f}%", fill="white")
                        self.draw_progress_bar(draw, 0, 25, 127, 7, cpu)

                        draw.text(
                            (0, 36),
                            f"MEM: {mem_pct:.1f}% ({mem_total}G)",
                            fill="white",
                        )
                        self.draw_progress_bar(draw, 0, 47, 127, 7, mem_pct)

                    # Page 1: Storage (SD / NVMe)
                    elif display_cycle == 1:
                        storage = self.get_storage_info()
                        if storage:
                            lbl = "NVME" if storage["is_root_nvme"] else "SD"
                            used_pct = storage["root_used_percent"]
                            total_gb = storage["root_total_gb"]

                            draw.text(
                                (0, 16),
                                f"{lbl}: {used_pct:.1f}% of {total_gb}G",
                                fill="white",
                            )
                            self.draw_progress_bar(
                                draw, 0, 28, 127, 8, used_pct
                            )

                            if (
                                not storage["is_root_nvme"]
                                and storage["nvme_info"]
                            ):
                                _, nvme_gb = storage["nvme_info"]
                                draw.text(
                                    (0, 44),
                                    f"NVMe: Mounted ({nvme_gb}G)",
                                    fill="white",
                                )
                            elif not storage["is_root_nvme"]:
                                draw.text(
                                    (0, 44),
                                    "NVMe: Not Detected",
                                    fill="white",
                                )

                    # Page 2: System Temperature
                    elif display_cycle == 2:
                        temp = self.get_temperature()
                        draw.text((20, 22), "TEMPERATURE", fill="white")
                        draw.rectangle(
                            (15, 36, 113, 56), outline="white", fill="black"
                        )
                        draw.text((32, 41), f"{temp:.1f} °C", fill="white")

                    # Page 3: Date & Time
                    else:
                        now = time.localtime()
                        date_str = time.strftime("%Y-%m-%d", now)
                        time_str = time.strftime("%H:%M:%S", now)

                        draw.text((32, 20), date_str, fill="white")
                        draw.text((40, 38), time_str, fill="white")

                time.sleep(1)

            except Exception as e:
                print(f"Runtime error: {e}")
                time.sleep(5)


if __name__ == "__main__":
    monitor = RPiSystemMonitor(bus_number=1, address=0x3C)
    monitor.run()