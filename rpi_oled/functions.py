#!/usr/bin/env python3
## get_ha_url.py
# Retrieves the configured Home Assistant Web UI URL from inside an Add-on container

import os
import requests


#: get_ha_url
#  Fetches internal_url/external_url from Core API or constructs a fallback URL
def get_ha_url():
    token = os.environ.get("SUPERVISOR_TOKEN")
    
    if not token:
        print("[ERROR] SUPERVISOR_TOKEN is missing. Ensure homeassistant_api: true is in config.json.")
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # 1. Fetch Core Config
    try:
        res = requests.get("http://supervisor/core/api/config", headers=headers, timeout=5)
        if res.status_code == 200:
            config = res.json()
            
            # Prefer external_url
            if config.get("external_url"):
                return config["external_url"]
    except Exception as e:
        print(f"[ERROR] Failed to query core config: {e}")

    # 2. Fallback: Query Core Info for port/ssl settings and build fallback URL
    try:
        res = requests.get("http://supervisor/core/info", headers=headers, timeout=5)
        if res.status_code == 200:
            core_info = res.json().get("data", {})
            port = core_info.get("port", 8123)
            scheme = "https" if core_info.get("ssl") else "http"
            
            # Try fetching primary host IP via Network API if hassio_api is enabled
            net_res = requests.get("http://supervisor/network/info", headers=headers, timeout=3)
            if net_res.status_code == 200:
                interfaces = net_res.json().get("data", {}).get("interfaces", [])
                for iface in interfaces:
                    if iface.get("state") == "connected" and iface.get("ipv4", {}).get("address"):
                        host_ip = iface["ipv4"]["address"][0].split("/")[0]
                        return f"{scheme}://{host_ip}:{port}"

            return f"{scheme}://homeassistant.local:{port}"
    except Exception as e:
        print(f"[ERROR] Fallback construction failed: {e}")

    return "http://homeassistant.local:8123?default_url_used"

#: get_entity_state
#  Queries Home Assistant API for a single entity state object given its entity ID
def get_entity_state(entity_id):
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        print("[ERROR] SUPERVISOR_TOKEN missing from environment.")
        return None

    url = f"http://supervisor/core/api/states/{entity_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        print(f"[FAIL] Query for '{entity_id}' returned HTTP {response.status_code}")
        return None
    except Exception as e:
        print(f"[ERROR] Connection failed for '{entity_id}': {e}")
        return None