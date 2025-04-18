import logging
import requests
import time
from homeassistant.components.valve import ValveEntity
from homeassistant import config_entries

_LOGGER = logging.getLogger(__name__)

# URL e headers per la comunicazione con il servizio
COOKIE_URL = "https://www.mysolem.com/login"
LOGIN_URL = "https://www.mysolem.com/login"
COMMAND_URL = "https://www.mysolem.com/module/sendManualModuleCommand"

HEADERS_LOGIN = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "www.mysolem.com",
    "Origin": "https://www.mysolem.com",
    "Referer": "https://www.mysolem.com/login",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}

def HEADERS_COMMAND(id_module, cookie):
    return {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Host": "www.mysolem.com",
        "Origin": "https://www.mysolem.com",
        "Referer": f"https://www.mysolem.com/module/{id_module}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": cookie
    }

async def async_setup_entry(hass, entry: config_entries.ConfigEntry, async_add_entities):
    """Setup della piattaforma valve basata sulla config entry."""
    username = entry.data["username"]
    password = entry.data["password"]
    zone = entry.data["zone"]
    module_id = entry.data["module_id"]
    serial_number = entry.data["serial_number"]

    _LOGGER.info("Setup irrigatore con utente: %s, zona: %s, modulo: %s, seriale: %s", username, zone, module_id, serial_number)

    async_add_entities([MyIrrigationValve(username, password, zone, module_id, serial_number)])





class MyIrrigationValve(ValveEntity):
    def __init__(self, username, password, zone, module_id, serial_number):
        self._attr_name = "Irrigatore MyIrrigation"
        self._attr_unique_id = f"myirrigation_{module_id}_{serial_number}"
        self._attr_supported_features = 0  # Nessuna funzionalità extra (come regolazione flusso)
        self._is_open = False
        self.username = username
        self.password = password
        self.zone = zone
        self.module_id = module_id
        self.serial_number = serial_number
        self._last_called = 0

    @property
    def is_open(self):
        return self._is_open

    @property
    def reports_position(self):
        # Imposta la posizione del report (ad esempio, se l'irrigatore è aperto o chiuso)
        return self._position

    async def async_open_valve(self, **kwargs):
        if self._can_execute_command():
            await self.hass.async_add_executor_job(self._send_command, "on")
            self._is_open = True
            self.async_write_ha_state()

    async def async_close_valve(self, **kwargs):
        _LOGGER.info("Chiamata async_close_valve()")
        if self._can_execute_command():
            _LOGGER.info("Esecuzione comando OFF")
            await self.hass.async_add_executor_job(self._send_command, "off")
            self._is_open = False
            self.async_write_ha_state()
        else:
            _LOGGER.info("Comando OFF ignorato: troppa frequenza")

    def _can_execute_command(self):
        current_time = time.time()
        if current_time - self._last_called > 60:
            self._last_called = current_time
            return True
        else:
            _LOGGER.warning("Comando ignorato: chiamata troppo frequente (deve passare almeno 60 secondi).")
            return False

    def _send_command(self, command):
        _LOGGER.info("Invio comando HTTP: %s", command)

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
                break

            except requests.exceptions.RequestException as e:
                _LOGGER.error("Errore durante l'invio del comando '%s': %s", command, e)
                if attempt < retries - 1:
                    _LOGGER.info("Riprovo tra 2 secondi (tentativo %d di %d)...", attempt + 2, retries)
                    time.sleep(2)
                else:
                    _LOGGER.error("Tentativi esauriti: comando '%s' non inviato.", command)
            finally:
                session.close()
