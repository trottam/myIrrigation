from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

DOMAIN = "myirrigation"

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Setup per la configurazione iniziale (quando non si usa un config entry)"""
    # La registrazione del flusso di configurazione è gestita automaticamente
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup quando un config entry viene aggiunto"""
    # Inoltra l'entry alla piattaforma "valve" in modo compatibile con HA 2025.6
    await hass.config_entries.async_forward_entry_setups(entry, ["valve"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unloading quando un config entry viene rimosso"""
    return await hass.config_entries.async_forward_entry_unload(entry, "valve")
