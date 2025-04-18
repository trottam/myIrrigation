from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
import voluptuous as vol
from homeassistant.exceptions import ConfigEntryNotReady

DOMAIN = "myirrigation"

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Required("zone"): str,
    vol.Required("module_id"): str,
    vol.Required("serial_number"): str
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce il flusso di configurazione per My Irrigation."""

    async def async_step_user(self, user_input=None):
        """Gestisce la configurazione da parte dell'utente."""
        if user_input is not None:
            try:
                return self.async_create_entry(title="My Irrigation", data=user_input)
            except ConfigEntryNotReady:
                return self.async_abort(reason="cannot_connect")
            except Exception as e:
                return self.async_show_form(
                    step_id="user",
                    data_schema=DATA_SCHEMA,
                    errors={"base": "unknown_error"}
                )

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)
