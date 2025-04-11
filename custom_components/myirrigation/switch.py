from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity
import requests
import time
import logging

_LOGGER = logging.getLogger(__name__)

# Costanti URL per la comunicazione con il servizio
COOKIE_URL = "https://www.myirrigationservice.com/signin"
LOGIN_URL = "https://www.myirrigationservice.com/signin"
COMMAND_URL = "https://www.myirrigationservice.com/api/irrigation/command"

class MyIrrigationSwitch(SwitchEntity):
    def __init__(self, hass, username, password, zone, module_id, serial_number):
        self.hass = hass
        self._attr_name = "Irrigatore MyIrrigation"
        self._is_on = False
        self.username = username
        self.password = password
        self.zone = zone
        self.module_id = module_id
        self.serial_number = serial_number
        self._last_called = 0  # Timestamp ultima chiamata

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        if self._can_execute_command():
            await self.hass.async_add_executor_job(self._send_command, "on")
            self._is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        if self._can_execute_command():
            await self.hass.async_add_executor_job(self._send_command, "off")
            self._is_on = False
            self.async_write_ha_state()

    def _can_execute_command(self):
        current_time = time.time()
        if current_time - self._last_called > 60:
            self._last_called = current_time
            return True
        else:
            _LOGGER.warning("Comando ignorato: chiamata troppo frequente (deve passare almeno 60 secondi).")
            return False

    def _send_command(self, command):
        retries = 3
        session = requests.Session()
        for attempt in range(retries):
            try:
                session.get(COOKIE_URL)
                cookie = session.cookies.get_dict()
                cookie_str = "; ".join(f"{k}={v}" for k, v in cookie.items())

                login_payload = {
                    "email": self.username,
                    "password": self.password,
                    "country-select": self.zone
                }

                login_response = session.post(
                    LOGIN_URL,
                    headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": cookie_str},
                    data=login_payload,
                    timeout=10
                )
                login_response.raise_for_status()

                command_payload = {
                    "moduleSerialNumber": self.serial_number,
                    "command": command,
                    "commandType": "status",
                    "commandParams": "0"
                }

                command_headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Cookie": cookie_str,
                    "Module-ID": self.module_id
                }

                response = session.post(
                    COMMAND_URL,
                    headers=command_headers,
                    data=command_payload,
                    timeout=10
                )
                response.raise_for_status()

                _LOGGER.debug("Comando '%s' inviato con successo: %s", command, response.text)
                break  # Comando riuscito, interrompi il ciclo

            except requests.exceptions.RequestException as e:
                _LOGGER.error("Errore durante l'invio del comando '%s': %s", command, e)
                if attempt < retries - 1:
                    _LOGGER.info("Riprovo tra 2 secondi (tentativo %d di %d)...", attempt + 2, retries)
                    time.sleep(2)
                else:
                    _LOGGER.error("Tentativi esauriti: comando '%s' non inviato.", command)
            finally:
                session.close()

async def async_setup_entry(hass, entry: ConfigEntry):
    # Creare l'entità quando viene configurata una nuova entry
    hass.data[DOMAIN] = MyIrrigationSwitch(
        hass,
        entry.data["username"],
        entry.data["password"],
        entry.data["zone"],
        entry.data["id_module"],
        entry.data["serial_number"]
    )
    return True
