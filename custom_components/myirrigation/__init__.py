from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_entry_flow
from homeassistant import config_entries
from .config_flow import ConfigFlow
from .valve import async_setup_entry

DOMAIN = "myirrigation"

async def async_setup(hass: HomeAssistant, config: dict):
    """Setup per la configurazione iniziale (quando non si usa un config entry)"""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setup quando un config entry viene aggiunto"""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "valve")
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unloading quando un config entry viene rimosso"""
    return await hass.config_entries.async_forward_entry_unload(entry, "valve")

# Registrazione del flusso di configurazione
async def async_register_config_flow(hass: HomeAssistant):
    """Registrazione del flusso di configurazione"""
    hass.config_entries.async_register_flow(DOMAIN, ConfigFlow)
