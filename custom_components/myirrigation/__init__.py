from homeassistant.core import HomeAssistant

DOMAIN = "myirrigation"

async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_setup_entry(hass: HomeAssistant, entry):
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "switch")
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    return await hass.config_entries.async_forward_entry_unload(entry, "switch")
