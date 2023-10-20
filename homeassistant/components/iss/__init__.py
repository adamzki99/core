"""The iss component."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from zoneinfo import ZoneInfo

import pyiss
import requests
from requests.exceptions import HTTPError
from skyfield.api import load, wgs84
from skyfield.sgp4lib import EarthSatellite
from skyfield.timelib import Time

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    OBSERVER_LATITUDE,
    OBSERVER_LONGITUDE,
    SATELLITE_NAME,
    STATIONS_URL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


@dataclass
class IssData:
    """Dataclass representation of data returned from pyiss."""

    number_of_people_in_space: int
    current_location: dict[str, str]
    iss_passes: dict[str, str]


class SatellitePass:
    """Class representing the next pass of the satellite."""

    next_rise: Time
    next_culmination: Time
    next_set: Time
    altitude: int
    azimuth: int


def update(iss: pyiss.ISS, skyfield_satellite_object: EarthSatellite) -> IssData:
    """Retrieve data from the pyiss API."""
    # Initialize return variables
    pass_details: list = []
    pass_count = 0
    event_names = ["rise above 15", "culminate", "set below 15"]

    # Define observer information
    observer_location = wgs84.latlon(OBSERVER_LATITUDE, OBSERVER_LONGITUDE)
    observer_timezone = ZoneInfo("Europe/Stockholm")

    now = datetime.now()
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )

    # Define a time range
    ts = load.timescale()
    t0 = ts.utc(now.year, now.month, now.day, 0)
    t1 = ts.utc(tomorrow.year, tomorrow.month, tomorrow.day, 23, 59, 59)

    # Find ISS passes
    t, events = skyfield_satellite_object.find_events(
        observer_location, t0, t1, altitude_degrees=15
    )

    # Iterate through passes and events
    for ti, event in zip(t, events):
        if event == 0:
            pass_count += 1
            pass_details.append({})
        event_name = event_names[event]
        local_time = ti.astimezone(observer_timezone)
        dt = local_time.strftime("%Y %b %d %H:%M:%S")
        alt, az, d = (skyfield_satellite_object - observer_location).at(ti).altaz()
        pass_details[pass_count - 1][event_name] = {
            "Datetime": dt,
            "Azimuth": az.degrees,
            "Altitude": alt.degrees,
        }

    return IssData(
        number_of_people_in_space=iss.number_of_people_in_space(),
        current_location=iss.current_location(),
        iss_passes=pass_details[0]["culminate"],
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})

    # satellites = await hass.async_add_executor_job(load.tle_file, (STATIONS_URL, reload=True))
    satellites = await hass.async_add_executor_job(load.tle_file, STATIONS_URL)

    by_name = {sat.name: sat for sat in satellites}
    satellite = by_name[SATELLITE_NAME]

    iss = pyiss.ISS()

    async def async_update() -> IssData:
        try:
            return await hass.async_add_executor_job(update, iss, satellite)
        except (HTTPError, requests.exceptions.ConnectionError) as ex:
            raise UpdateFailed("Unable to retrieve data") from ex

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update,
        update_interval=timedelta(seconds=60),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN] = coordinator

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        del hass.data[DOMAIN]
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
