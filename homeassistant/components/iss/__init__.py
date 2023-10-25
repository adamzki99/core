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
    ALTIUDE_DEGREES,
    CET_TIMEZONE,
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


def define_time_range(now: datetime) -> tuple:
    """Define a time range spanning from the current time to the end of the next day.

    Returns a tuple containing two datetime objects representing the start and end of the time range.

    The time range starts from the current time and ends at 23:59:59 of the next day.

    Returns:
        tuple: A tuple containing two datetime objects.
            The first element is the current time.
            The second element is the end time of the next day.
    """
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )

    # Define a time range
    local_timescale = load.timescale()

    current_time = local_timescale.utc(
        now.year, now.month, now.day, now.hour, now.minute, now.second
    )
    next_day_time = local_timescale.utc(
        tomorrow.year, tomorrow.month, tomorrow.day, 23, 59, 59
    )

    return current_time, next_day_time


def define_observer_information(
    observer_latitude: float, observer_longitude: float, timezone: str
) -> tuple:
    """Define observer information for a specific location and timezone.

    Args:
        observer_latitude (float): The latitude of the observer's location.
        observer_longitude (float): The longitude of the observer's location.
        timezone (str): The timezone identifier for the observer's location (e.g., 'America/New_York').

    Returns:
        tuple: A tuple containing two objects.
            The first element is a WGS84 LatitudeLongitude object representing the observer's location.
            The second element is a ZoneInfo object representing the observer's timezone.
    """
    return wgs84.latlon(observer_latitude, observer_longitude), ZoneInfo(timezone)


def get_pass_details(
    t: list,
    events: list,
    observer_timezone: ZoneInfo,
    observer_location,
    skyfield_satellite_object,
) -> list:
    """Get details about satellite passes for a specific observer.

    Args:
        t (list): A list of times for the satellite events.
        events (list): A list of event codes corresponding to each time in 't'.
        observer_timezone (ZoneInfo): The timezone information for the observer.
        observer_location: The geographic location of the observer.
        skyfield_satellite_object: A Skyfield satellite object representing the satellite of interest.

    Returns:
        list: A list of dictionaries containing pass details.
    """

    # Initialize local variables
    pass_details: list = []
    pass_count = 0
    event_names = [
        f"rise above {ALTIUDE_DEGREES}",
        "culminate",
        f"set below {ALTIUDE_DEGREES}",
    ]

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

    return pass_details


def update(iss: pyiss.ISS, skyfield_satellite_object: EarthSatellite) -> IssData:
    """Update and retrieve data from the pyiss API for the International Space Station (ISS).

    Args:
        iss (pyiss.ISS): An instance of the pyiss.ISS class for ISS data retrieval.
        skyfield_satellite_object (EarthSatellite): A Skyfield EarthSatellite object representing the ISS.

    Returns:
        IssData: An IssData object containing updated information.
    """

    observer_location, observer_timezone = define_observer_information(
        OBSERVER_LATITUDE, OBSERVER_LONGITUDE, CET_TIMEZONE
    )

    current_time, next_day_time = define_time_range(datetime.now())

    # Find ISS passes
    t, events = skyfield_satellite_object.find_events(
        observer_location, current_time, next_day_time, altitude_degrees=ALTIUDE_DEGREES
    )

    pass_details = get_pass_details(
        t, events, observer_timezone, observer_location, skyfield_satellite_object
    )

    return IssData(
        number_of_people_in_space=iss.number_of_people_in_space(),
        current_location=iss.current_location(),
        iss_passes=pass_details[0]["culminate"],
    )


def load_satellites() -> list:
    """Load the lists of available satellites from the Skyfield API."""
    return load.tle_file(STATIONS_URL)


def select_satellite(satellites: list, satellite_name: str):
    """Select a specific satellite by name.

    Args:
        satellites (list): Lists of satellites loaded using load_satellites()
        satellite_name (str): The desired satellite object to select
    """

    by_name = {sat.name: sat for sat in satellites}
    return by_name[satellite_name]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})

    # satellites = await hass.async_add_executor_job(load.tle_file, (STATIONS_URL, reload=True))
    satellites = await hass.async_add_executor_job(load_satellites)
    satellite = await hass.async_add_executor_job(
        select_satellite, satellites, SATELLITE_NAME
    )

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
