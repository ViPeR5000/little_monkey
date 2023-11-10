"""DataUpdateCoordinator for little_monkey."""
from __future__ import annotations

from datetime import timedelta
from homeassistant.util import json

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import (
    LittleMonkeyApiClient,
    LittleMonkeyApiClientAuthenticationError,
    LittleMonkeyApiClientError,
)
from .const import (
    DOMAIN,
    CONF_LANG,
    POLL_INTERVAL,
    LOGGER
)

# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class LittleMonkeyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Ecojoko APIs."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: LittleMonkeyApiClient,
    ) -> None:
        """Initialize."""
        self.hass = hass
        self.config_entry = entry
        self.client = client
        LOGGER.debug("OPTIONS: %s", entry.options)
        self._lang = entry.options[CONF_LANG]
        self._tranfile = self.get_tran_file()

        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_method=self._async_update_data,
            update_interval=timedelta(seconds=int(entry.data.get(POLL_INTERVAL))),
        )

    @property
    def tranfile(self):
        """get tranflie"""
        return self._tranfile

    def get_tran_file(self):
        """get translation file for wupws sensor friendly_name"""
        tfiledir = f'custom_components/{DOMAIN}/{DOMAIN}_translations/'
        tfilename = self._lang.split('-', 1)[0]
        try:
            tfiledata = json.load_json(f'{tfiledir}{tfilename}.json')
        except Exception:  # pylint: disable=broad-except
            tfiledata = json.load_json(f'{tfiledir}en.json')
            LOGGER.warning(
                'Sensor translation file %s.json does not exist. Defaulting to en-US.',
                 tfilename.keys)
        return tfiledata

    async def _async_update_data(self):
        """Update data via library."""
        try:
            await self.client.async_get_data()
            data = {
                "realtime_consumption" : self.client.realtime_conso,
                "grid_consumption": self.client.kwh,
                "hc_grid_consumption": self.client.kwh_hc_ns,
                "hp_grid_consumption": self.client.kwh_hp_ns,
                "blue_hc_grid_consumption": self.client.tempo_hc_blue,
                "blue_hp_grid_consumption": self.client.tempo_hp_blue,
                "white_hc_grid_consumption": self.client.tempo_hc_white,
                "white_hp_grid_consumption": self.client.tempo_hp_white,
                "red_hc_grid_consumption": self.client.tempo_hc_red,
                "red_hp_grid_consumption": self.client.tempo_hp_red,
                "production_surplus": self.client.kwh_prod,
                "indoor_temp": self.client.indoor_temp,
                "outdoor_temp": self.client.outdoor_temp,
                "indoor_hum": self.client.indoor_hum,
                "outdoor_hum": self.client.outdoor_hum,
            }
            self.data = data
            return data
        except LittleMonkeyApiClientAuthenticationError as exception:
            LOGGER.error("COORDINATOR API client authentication error: %s", exception)
            raise ConfigEntryAuthFailed(exception) from exception
        except LittleMonkeyApiClientError as exception:
            LOGGER.error("COORDINATOR API client error: %s", exception)
            raise UpdateFailed(exception) from exception
        except Exception as exception:  # pylint: disable=broad-except
            LOGGER.error("COORDINATOR other error: %s", exception)
            raise UpdateFailed(exception) from exception
