import logging
import requests
import time
from homeassistant.components.switch import SwitchEntity

_LOGGER = logging.getLogger(__name__)

COOKIE_URL = "https://www.myirrigationservice.com/signin"
LOGIN_URL = "https://www.myirrigationservice.com/signin"
COMMAND_URL = "https://www.myirrigationservice.com/api/irrigation/command"

HEADERS_LOGIN = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0",
}

def HEADERS_COMMAND(module_id, cookie_str):
    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.myirrigationservice.com/dashboard",
        "Cookie": cookie_str,
        "X-Requested-With": "XMLHttpRequest",
        "Module-ID": module_id,
    }

def setup_platform(hass, config, add_entities, discovery_info=None):
    username = config.get("username")
    password = config.get("password")
    zone = config.get("zone")
    module_id = config.get("module_id")
    serial_number = config.get("serial_number")
    
    add_entities([MyIrrigationSwitch(username, password, zone, module_id, serial_number)])

class MyIrrigationSwitch(SwitchEntity):
    def __init__(self, username, password, zone, module_id, serial_number):
        self._attr_name = "Irrigatore MyIrrigation"
        self._is_on = False
        self.username = username
        self.password = password
        self.zone = zone
        self.module_id = module_id
        self.serial_number = serial_number
        self._last_called = 0  # Timestamp ultima chiamata

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
        for attempt in range(retries):
            session = requests.Session()
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
                    headers={**HEADERS_LOGIN, "Cookie": cookie_str},
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

                command_headers = HEADERS_COMMAND(self.module_id, cookie_str)

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
