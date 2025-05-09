from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_entry_flow
from .config_flow import ConfigFlow

DOMAIN = "myirrigation"

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Setup per la configurazione iniziale (quando non si usa un config entry)"""
    # Registra il flusso di configurazione
    config_entry_flow.register(DOMAIN, ConfigFlow)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup quando un config entry viene aggiunto"""
    # Inoltra l'entry alla piattaforma "valve" in modo compatibile con HA 2025.6
    await hass.config_entries.async_forward_entry_setups(entry, ["valve"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unloading quando un config entry viene rimosso"""
    return await hass.config_entries.async_forward_entry_unload(entry, "valve")
