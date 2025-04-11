import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.exceptions import ConfigEntryNotReady

DOMAIN = "myirrigation"

# Schema dei dati richiesti per la configurazione
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
            # Qui puoi aggiungere ulteriori validazioni, come controllare che
            # l'utente possa connettersi all'API di My Irrigation, ad esempio.
            try:
                # Esegui una prova di connessione o validazione (es. controllo credenziali)
                # Ad esempio:
                # if not self._check_credentials(user_input[CONF_USERNAME], user_input[CONF_PASSWORD]):
                #     raise InvalidAuth  # Se le credenziali sono errate

                # Creazione dell'entry con i dati forniti dall'utente
                return self.async_create_entry(title="My Irrigation", data=user_input)
            except ConfigEntryNotReady:
                # Gestione degli errori (se l'API non è pronta o c'è un problema di connessione)
                return self.async_abort(reason="cannot_connect")
            except Exception as e:
                # Gestione di altri errori generici
                return self.async_show_form(
                    step_id="user",
                    data_schema=DATA_SCHEMA,
                    errors={"base": "unknown_error"}
                )

        # Se non sono stati forniti input, mostra il modulo per raccogliere i dati
        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)
