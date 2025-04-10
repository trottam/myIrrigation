import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD

DOMAIN = "myirrigation"

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Required("zone"): str,
    vol.Required("id_module"): str,
    vol.Required("serial_number"): str
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="My Irrigation", data=user_input)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)
