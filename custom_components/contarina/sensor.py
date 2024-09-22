from datetime import datetime, timedelta, timezone, UTC
from enum import Enum
import json
import logging
from pathlib import Path

import requests
import voluptuous as vol

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

# URL dell'API da chiamare
CONF_API_URL = "api_url"
DEFAULT_NAME = "API Sensor"
CONF_ZONE_ID = "zone_id"

# Definiamo lo schema della configurazione
CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_URL): cv.string,
        vol.Required(CONF_ZONE_ID): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    },
    extra=vol.ALLOW_EXTRA,
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Configura la piattaforma del sensore."""
    api_url = config.get(CONF_API_URL)
    name_prossimo_svuotamento = config.get(CONF_NAME)
    zone_id = config.get(CONF_ZONE_ID)
    unique_id_prossimo_svuotamento = (
        f"contarina_{name_prossimo_svuotamento.lower().replace(' ','_')}_{zone_id}"
    )

    name_prossimo_svuotamento = "Prossimo Svuotamento"
    unique_id_prossimo_svuotamento = (
        f"contarina_{name_prossimo_svuotamento.lower().replace(' ','_')}_{zone_id}"
    )
    prossimo_svuotamento = APISensor(
        name_prossimo_svuotamento,
        api_url,
        zone_id,
        unique_id_prossimo_svuotamento,
        EmptyingSensorType.NextEmptying,
    )

    name_svuotamento_di_oggi = "Svuotamento di Oggi"
    unique_id_svuotamento_di_oggi = (
        f"contarina_{name_svuotamento_di_oggi.lower().replace(' ','_')}_{zone_id}"
    )
    svuotamento_di_oggi = APISensor(
        name_svuotamento_di_oggi,
        api_url,
        zone_id,
        unique_id_svuotamento_di_oggi,
        EmptyingSensorType.TodayEmptying,
    )

    add_entities([prossimo_svuotamento, svuotamento_di_oggi], True)


class APISensor(SensorEntity):
    """Implementa il sensore per fare la chiamata API e restituire il JSON."""

    def __init__(self, name, api_url, zone_id, unique_id, type_of_sensor):
        """Inizializza il sensore."""
        self._name = name
        self._api_url = api_url
        self._zone_id = zone_id
        self._unique_id = unique_id
        self._type_of_sensor = type_of_sensor
        self._state = None
        self._attributes = {}
        self._last_api_call = None

        data_dir = Path("config/.storage/contarina")
        data_dir.mkdir(parents=True, exist_ok=True)

        self._file_path = data_dir / "ecocalendari.json"

        _LOGGER.error("Zone ID: %s", self._zone_id)

    @property
    def name(self):
        """Restituisce il nome del sensore."""
        return self._name

    @property
    def state(self):
        """Restituisce lo stato attuale (in questo caso, il JSON come stringa)."""
        return self._state

    @property
    def zone_id(self):
        """Restituisce lo stato attuale (in questo caso, il JSON come stringa)."""
        return self._zone_id

    @property
    def extra_state_attributes(self):
        """Restituisce gli attributi extra del sensore."""
        return self._attributes

    @property
    def unique_id(self):
        """Restituisce l'ID unico del sensore."""
        return self._unique_id

    @property
    def last_api_call(self):
        """Return the last time the API have been called."""
        return self._last_api_call

    def update(self, now=None):
        """Esegui l'aggiornamento dei dati chiamando l'API."""
        try:
            if (
                (self.last_api_call is None)
                or (
                    datetime.__sub__(datetime.now(), self.last_api_call)
                    > timedelta(days=1)
                )
                or not (self._file_path.exists())
            ):
                response = requests.get(self._api_url, timeout=10)
                response.raise_for_status()

                self._last_api_call = datetime.now()
                data = response.json()
                json_string = json.dumps(data)
                save_string_to_file(self, json.dumps(data))
                _LOGGER.info(
                    "Rquested Ecocalendari form contarina API %s", datetime.now()
                )

                emptyingsDays = deserializeEmptyingDays(json_string)
            else:
                json_file_content = read_string_from_file(self)
                emptyingsDays = deserializeEmptyingDays(json_file_content)

            emptyingsDays = getRequestedZone(emptyingsDays, self.zone_id)

            if self._type_of_sensor == EmptyingSensorType.NextEmptying:
                day_of_emptying = get_next_emptying(emptyingsDays, self._zone_id)
            else:
                day_of_emptying = get_emptying_to_be_done(emptyingsDays, self._zone_id)

            if day_of_emptying is not None:
                emptyings = day_of_emptying.emptyings
                emptyings = emptyings.replace("1", "Secco")
                emptyings = emptyings.replace("2", "Vegetale")
                emptyings = emptyings.replace("3", "Umido")
                emptyings = emptyings.replace("4", "VPL")
                emptyings = emptyings.replace("5", "Carta")

                self._state = emptyings
                self._attributes = {
                    "Date": day_of_emptying.date,
                    "Zone ID": self.zone_id,
                }
            else:
                self._state = ""
                self._attributes = {
                    "Date": "",
                    "Zone ID": "",
                }

        except requests.exceptions.RequestException as e:
            _LOGGER.error("Errore nella chiamata API: %s", e)
            self._state = None


class EmptyingDay:
    """Describe the emptying day, with emptyings and id of the zone."""

    def __init__(
        self, id, ecocalendario_id, giorno, last_update, cancellato, svuotamenti
    ):
        self.id = id
        self.idEcocalendario = ecocalendario_id
        self.dayTimestamp = giorno
        self.lastUpdateTimestamp = last_update
        self.canceled = cancellato
        self.emptyings = svuotamenti
        self.date = datetime.fromtimestamp(self.dayTimestamp, UTC).astimezone(
            datetime.now().tzinfo
        )

    def __repr__(self) -> str:
        return f"EmptyingDay(id={self.id}, idEcocalendario={self.idEcocalendario})"


class EmptyingSensorType(Enum):
    """Define the type of sensor."""

    NextEmptying = 1
    TodayEmptying = 2


def deserializeEmptyingDays(jsonString):
    data = json.loads(jsonString)
    emptyingDays = [
        EmptyingDay(
            d["id"],
            d["ecocalendario_id"],
            d["giorno"],
            d["last_update"],
            d["cancellato"],
            d["svuotamenti"],
        )
        for d in data
    ]
    return sorted(emptyingDays, key=lambda day: day.date)


def getRequestedZone(emptyingDays: list[EmptyingDay], zone) -> list[EmptyingDay]:
    """Get Requested Zone"""
    daysOfRequestedZone = [day for day in emptyingDays if day.idEcocalendario == zone]
    return daysOfRequestedZone


def get_next_emptying(emptyingDays: list[EmptyingDay], zone_id):
    """Get next emptying"""
    return [
        day
        for day in emptyingDays
        if day.idEcocalendario == zone_id and day.emptyings != ""
    ][0]


def get_emptying_to_be_done(emptyingDays: list[EmptyingDay], zone_id) -> EmptyingDay:
    """Get emptying to be done."""
    today = datetime.now()
    if today.hour >= 12:
        giorni = [
            day
            for day in emptyingDays
            if day.idEcocalendario == zone_id
            and day.date.date() == (today + timedelta(days=1)).date()
        ]
        if len(giorni) >= 1:
            return giorni[0]
        return None

    giorni = [
        day
        for day in emptyingDays
        if day.idEcocalendario == zone_id and day.date.date() == today.date()
    ]
    if len(giorni) >= 1:
        return giorni[0]
    return None


def save_string_to_file(self, stringToWrite):
    """Salva la stringa JSON in un file."""
    try:
        with Path.open(self._file_path, "w") as json_file:
            json_file.write(stringToWrite)
    except OSError as e:
        _LOGGER.error(f"Errore durante il salvataggio del file JSON: {e}")


def read_string_from_file(self) -> str:
    """Legge il file JSON e restituisce i dati."""
    try:
        if self._file_path.exists():
            return self._file_path.read_text()
        else:
            _LOGGER.error("Il file %s non esiste.", self._file_path)
            return None
    except OSError as e:
        _LOGGER.error("Errore durante la lettura del file JSON: '%s'", e)
        return None
