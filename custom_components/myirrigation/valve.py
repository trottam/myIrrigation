import logging
import requests
import time
import asyncio
from homeassistant.components.valve import ValveEntity, ValveEntityFeature
from homeassistant import config_entries
from homeassistant.helpers.entity import EntityDescription
from homeassistant.const import STATE_OPEN, STATE_CLOSED
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

MODULE_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
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
        self._position = 0
        self._attr_should_poll = False
        self._attr_supported_features = (
            ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE
        )

    @property
    def state(self):
        """Ritorna lo stato dell'entità, in base alla posizione."""
        return STATE_OPEN if self._position == 1 else STATE_CLOSED

    @property
    def is_open(self):
        """Restituisce se la valvola è aperta."""
        return self._is_open

    @property
    def current_valve_position(self):
        """Restituisce la posizione attuale della valvola."""
        return self._position

    @property
    def reports_position(self):
        """Restituisce la posizione della valvola."""
        if self._position is None:
            _LOGGER.warning("La posizione non è stata impostata per %s", self.entity_id)
            return 0  # Fallback al valore di 0 se _position è None
        return self._position

    async def async_update(self):
        """Aggiorna lo stato della valvola. Viene chiamato solo da HA sotto esplicita chiamata"""
        _LOGGER.debug("Chiamato async_update per %s", self.entity_id)
        result = await self.hass.async_add_executor_job(self._get_valve_status)
        if result is not None:
            self._is_open = result
            self._position = 1 if result else 0

    def _get_valve_status(self):
        """Interroga il portale per sapere se la valvola è aperta."""
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

                modules_api_url = f"https://www.mysolem.com/remote/module/state?moduleId={self.module_id}"
                response = session.get(
                    modules_api_url, 
                    headers={**MODULE_HEADERS, "Cookie": cookie_str, "Referer":modules_api_url}, 
                    data = self.module_id
                )

                response.raise_for_status()
                
                waterData=response.json();
                watering = waterData['status']['watering']
                running_program = watering['runningProgram']
                running_station = watering['runningStation']
                state = watering['state']
                
                _LOGGER.debug("Comando '%s' inviato con successo", response.text)
                if any(val != 0 for val in [running_program, running_station]):
                    return True  # Ritorna True se solo se la risposta è positiva
            except requests.exceptions.RequestException as e:
                _LOGGER.error("Errore durante l'invio del comando: %s", e)
                if attempt < retries - 1:
                    _LOGGER.info("Riprovo tra 2 secondi (tentativo %d di %d)...", attempt + 2, retries)
                    time.sleep(2)
                else:
                    _LOGGER.error("Tentativi esauriti: comando '%s' non inviato.")
            finally:
                session.close()
        return False  # Ritorna False se non è riuscito a inviare il comando
    
    async def async_turn_on(self, **kwargs):
        """Apre la valvola."""
        if self._can_execute_command():
            result = await self.hass.async_add_executor_job(self._send_command, "on")
            if result:
                self._is_open = True
                self._position = 1
                self.async_write_ha_state()

#    async def async_turn_off(self, **kwargs):
#        """Chiude la valvola."""
#        if self._can_execute_command():
#            result = await self.hass.async_add_executor_job(self._send_command, "off")
#            if result:
#                self._is_open = False
#                self._position = 0
#                self.async_write_ha_state()

    async def async_turn_off(self, retries=3, **kwargs):
        """Chiude la valvola."""
        if self._can_execute_command():
            result = await self.hass.async_add_executor_job(self._send_command, "off")
            if result:
                self._is_open = False
                self._position = 0
                self.async_write_ha_state()
        elif retries > 0:
            _LOGGER.warning("Comando OFF ignorato, ritento tra 60 secondi. Tentativi rimasti: %s", retries)
            self.hass.async_create_task(self._retry_async_turn_off(retries - 1))

    async def _retry_async_turn_off(self, retries):
        await asyncio.sleep(60)
        await self.async_turn_off(retries=retries)

    async def async_open_valve(self, **kwargs):
        """Apre la valvola."""
        await self.async_turn_on()

    async def async_close_valve(self, **kwargs):
        """Chiude la valvola."""
        await self.async_turn_off()

    def _can_execute_command(self):
        """Controlla se è possibile eseguire il comando."""
        current_time = time.time()
        if current_time - self._last_called > 60:
            self._last_called = current_time
            return True
        else:
            _LOGGER.warning("Comando ignorato: chiamata troppo frequente (deve passare almeno 60 secondi).")
            return False

    def _send_command(self, command):
        """Invia il comando al modulo remoto."""
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
                    "commandParams": "1"
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
                return True  # Ritorna True solo se la risposta è positiva
            except requests.exceptions.RequestException as e:
                _LOGGER.error("Errore durante l'invio del comando: %s", command, e)
                if attempt < retries - 1:
                    _LOGGER.info("Riprovo tra 2 secondi (tentativo %d di %d)...", attempt + 2, retries)
                    time.sleep(2)
                else:
                    _LOGGER.error("Tentativi esauriti: comando '%s' non inviato.", command)
            finally:
                session.close()

        return False  # Ritorna False se non è riuscito a inviare il comando
