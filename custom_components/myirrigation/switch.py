import logging
import requests
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

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

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    data = config_entry.data
    switch = MyIrrigationSwitch(
        username=data["username"],
        password=data["password"],
        zone=data["zone"],
        module_id=data["id_module"],
        serial_number=data["serial_number"]
    )
    async_add_entities([switch])


class MyIrrigationSwitch(SwitchEntity):
    def __init__(self, username, password, zone, module_id, serial_number):
        self._attr_name = "Irrigatore MyIrrigation"
        self._is_on = False
        self.username = username
        self.password = password
        self.zone = zone
        self.module_id = module_id
        self.serial_number = serial_number

    @property
    def is_on(self) -> bool:
        return self._is_on

    def turn_on(self, **kwargs):
        self._send_command("on")
        self._is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        self._send_command("off")
        self._is_on = False
        self.schedule_update_ha_state()

    def _send_command(self, command: str):
        session = requests.Session()
        session.get(COOKIE_URL)
        cookie = session.cookies.get_dict()
        cookie_str = "; ".join(f"{k}={v}" for k, v in cookie.items())

        login_payload = {
            "email": self.username,
            "password": self.password,
            "country-select": self.zone
        }

        session.post(LOGIN_URL, headers={**HEADERS_LOGIN, "Cookie": cookie_str}, data=login_payload)

        command_payload = {
            "moduleSerialNumber": self.serial_number,
            "command": command,
            "commandType": "status",
            "commandParams": "0"
        }

        command_headers = HEADERS_COMMAND(self.module_id, cookie_str)
        response = session.post(COMMAND_URL, headers=command_headers, data=command_payload)
        _LOGGER.debug("Comando inviato: %s", response.text)
