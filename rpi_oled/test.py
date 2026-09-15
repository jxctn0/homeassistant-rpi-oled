import os

#: get_hass_url
#  Returns the Home Assistant URL base depending on environment context
def get_hass_url(default_url="http://localhost:8123"):
    # If running inside a Home Assistant Add-on container, use the Supervisor proxy
    if os.environ.get("SUPERVISOR_TOKEN"):
        return "http://supervisor/core"
    
    # Fallback to HASS_SERVER env var, or the specified default URL
    return os.environ.get("HASS_SERVER", default_url)