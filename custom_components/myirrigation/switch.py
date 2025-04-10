import logging
import requests
from homeassistant.components.switch import SwitchEntity

_LOGGER = logging.getLogger(__name__)

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

HEADERS_COMMAND = lambda id_module, cookie: {
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

class MyIrrigationSwitch(SwitchEntity):
    def __init__(self, username, password, zone, module_id, serial_number):
        self._attr_name = "Irrigatore MyIrrigation"
        self._is_on = False
        self.username = username
        self.password = password
        self.zone = zone
        self.module_id = module_id
        self.serial_number = serial_number

    async def async_turn_on(self, **kwargs):
        await self.hass.async_add_executor_job(self._send_command, "on")
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self.hass.async_add_executor_job(self._send_command, "off")
        self._is_on = False
        self.async_write_ha_state()

    @property
    def is_on(self):
        return self._is_on

    def _send_command(self, command):
        try:
            session = requests.Session()
            session.get(COOKIE_URL)
            cookie = session.cookies.get_dict()
            cookie_str = "; ".join(f"{k}={v}" for k, v in cookie.items())

            login_payload = {
                "email": self.username,
                "password": self.password,
                "country-select": self.zone
            }

            login_response = session.post(LOGIN_URL, headers={**HEADERS_LOGIN, "Cookie": cookie_str}, data=login_payload)
            login_response.raise_for_status()

            command_payload = {
                "moduleSerialNumber": self.serial_number,
                "command": command,
                "commandType": "status",
                "commandParams": "0"
            }

            command_headers = HEADERS_COMMAND(self.module_id, cookie_str)
            response = session.post(COMMAND_URL, headers=command_headers, data=command_payload)
            response.raise_for_status()

            _LOGGER.debug("Comando inviato con successo: %s", response.text)

        except requests.exceptions.RequestException as e:
            _LOGGER.error("Errore durante l'invio del comando %s: %s", command, e)
            
async def async_setup_entry(hass: HomeAssistant, entry):
    username = entry.data.get("username")
    password = entry.data.get("password")
    zone = entry.data.get("zone")
    module_id = entry.data.get("id_module")
    serial_number = entry.data.get("serial_number")

    # Crea il dispositivo (entità)
    switch = MyIrrigationSwitch(hass, username, password, zone, module_id, serial_number)
    hass.data.setdefault("myirrigation", {})[entry.entry_id] = switch

    # Registrare il dispositivo nell'integrazione
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "switch")
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload the entry."""
    hass.data["myirrigation"].pop(entry.entry_id)
    return await hass.config_entries.async_forward_entry_unload(entry, "switch")
