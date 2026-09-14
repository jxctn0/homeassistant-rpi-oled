#!/usr/bin/env python3
import psutil
import time
import json

try:
    from smbus2 import SMBus
except ImportError:
    try:
        from smbus import SMBus
    except ImportError:
        print("Error: smbus2 or smbus not found")
        exit(1)

import os
import subprocess
from pathlib import Path

OLED_MAPPINGS = {
    "ssd1306": 0x3C
}

class RPiSystemMonitor:
    def __init__(self):
        # Import user config
        with open("/data/options.json") as cf:
            config = json.load(cf)
        
        i2c_bus = config["i2c_bus"]
        oled_type = config["oled_type"]
        print("oled_type: "+ oled_type)
        oled_address = OLED_MAPPINGS[oled_type]

        # Initialize i2c bus with config
        try:
            self.bus = SMBus(i2c_bus)
            self.i2c_address = 0x3c # displays may vary! If yours uses a different address, please pull an issue and I will make a pull for it!
        except Exception as e:
            print(f"i2c Init Error: {e}")
            self.bus = None


    def get_cpu_usage(self):
        """Get CPU usage percentage"""
        return psutil.cpu_percent(interval=1)

    def get_memory_info(self):
        """Get memory usage information"""
        mem = psutil.virtual_memory()
        total_gb = round(mem.total / (1024**3), 1)  # Convert to GB
        return mem.percent, total_gb

    def get_temperature(self):
        """Get Pi's temperature"""
        try:
            # Try multiple thermal zones common on RPi
            zones = ["/sys/class/thermal/thermal_zone0/temp", "/sys/class/thermal/thermal_zone1/temp"]
            for zone in zones:
                if os.path.exists(zone):
                    with open(zone, "r") as f:
                        temp = float(f.read().strip()) / 1000
                    return temp
            return -1
        except:
            return -1

    def get_root_device(self):
        """Get the device where root (/) is mounted"""
        try:
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    device, mount_point, *_ = line.split()
                    if mount_point == '/':
                        return device
            return None
        except Exception as e:
            return None

    def get_storage_info(self):
        """Get storage information for root directory"""
        try:
            root_disk = psutil.disk_usage('/')
            root_total_gb = round(root_disk.total / (1024**3), 1)
            root_used_percent = root_disk.percent
            root_device = self.get_root_device()

            return {
                'root_used_percent': root_used_percent,
                'root_total_gb': root_total_gb,
            }
        except Exception as e:
            return None

    def send_to_oled(self, x, y, message):
        """Send data to OLED display"""
        if not self.bus: return
        try:
            data = [x, y] + list(message.encode('ascii'))
            self.bus.write_i2c_block_data(self.i2c_address, 0x00, data)
            time.sleep(0.01)
        except Exception as e:
            print(f"Send data error: {e}")

    def send_big_to_oled(self, x, y, message):
        """Send data to OLED display"""
        if not self.bus: return
        try:
            data = [x, y] + list(message.encode('ascii'))
            self.bus.write_i2c_block_data(self.i2c_address, 0x01, data)
            time.sleep(0.01)
        except Exception as e:
            print(f"Send data error: {e}")

    def send_progress_to_oled(self, y, progress):
        """Send data to OLED display"""
        if not self.bus: return
        try:
            data = [0xFF, 0xF0, y, progress]
            self.bus.write_i2c_block_data(self.i2c_address, 0x00, data)
            time.sleep(0.01)
        except Exception as e:
            print(f"Send progress error: {e}")

    def clear_screen(self):
        """Clear OLED screen"""
        if not self.bus: return
        try:
            self.bus.write_i2c_block_data(self.i2c_address, 0x00, [0xFF, 0xFF])
            time.sleep(0.01)
        except Exception as e:
            print(f"Clear screen error: {e}")

    def run(self):
        """Main running loop"""
        display_cycle = 0
        cycle_start_time = time.time()
        empty_line = " ".ljust(19)

        while True:
            try:

                current_time = time.time()
                print(f"DEBUG: {current_time}")
                
                if display_cycle < 2:
                    if current_time - cycle_start_time >= 8:
                        cycle_start_time = current_time
                        display_cycle = (display_cycle + 1) % 4
                        if display_cycle != 0: self.clear_screen()
                else:
                    if current_time - cycle_start_time >= 5:
                        cycle_start_time = current_time
                        display_cycle = (display_cycle + 1) % 4
                        if display_cycle != 0: self.clear_screen()

                if display_cycle == 0:
                    cpu_usage = self.get_cpu_usage()
                    mem_usage, mem_total = self.get_memory_info()
                    cpu_msg = f"CPU:{cpu_usage:.1f}%".ljust(19)
                    mem_msg = f"MEM:{mem_usage:.1f}% => {mem_total}G".ljust(19)
                    self.send_to_oled(0, 0, cpu_msg)
                    self.send_progress_to_oled(1, int(cpu_usage))
                    self.send_to_oled(0, 2, empty_line)
                    self.send_to_oled(0, 3, mem_msg)
                    self.send_progress_to_oled(4, int(mem_usage))

                elif display_cycle == 1:
                    storage_info = self.get_storage_info()
                    if storage_info:
                        sd_msg = f"SD:{storage_info['root_used_percent']:.1f}% => {storage_info['root_total_gb']}G".ljust(19)
                        self.send_to_oled(0, 1, sd_msg)
                        self.send_progress_to_oled(2, int(storage_info['root_used_percent']))

                elif display_cycle == 2:
                    temperature = self.get_temperature()
                    temp_msg = f"TEMP: {temperature:.1f}C".center(14)
                    self.send_big_to_oled(0, 2, temp_msg)
                    self.send_big_to_oled(0, 2, temp_msg)

                else:
                    current_datetime = time.localtime()
                    date_msg = time.strftime("  %Y/%m/%d", current_datetime).ljust(14)
                    time_msg = time.strftime("     %H:%M", current_datetime).ljust(14)
                    self.send_big_to_oled(0, 1, date_msg)
                    self.send_big_to_oled(0, 3, time_msg)

                time.sleep(1)

            except Exception as e:
                print(f"Runtime error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    monitor = RPiSystemMonitor()
    monitor.run()
