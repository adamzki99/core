"""Functions used to get the position of a satellite from a specific UTC time."""

from skyfield.api import load

from .const import SATELLITE_NAME, STATIONS_URL


def load_satellites(satellite_name: str):
    """Load satellite data and retrieve information for a specific satellite by name.

    This function loads Two-Line Element Set (TLE) satellite data from a specified source and retrieves
    information for a satellite with the given name.

    Args:
        satellite_name (str): The name of the satellite for which you want to retrieve TLE data.
    """
    satellites = load.tle_file(STATIONS_URL)

    by_name = {sat.name: sat for sat in satellites}
    return by_name[satellite_name]


def get_iss_position(
    year: int, month: int, day: int, hour: int, minute: int, second: int
) -> list:
    """Get the International Space Station (ISS) geocentric position at a specific date and time.

    This function calculates the geocentric position of the ISS (International Space Station) at a given date and time.
    The position is returned as a list of coordinates in kilometers.

    Args:
        year (int): The year of the desired date.
        month (int): The month of the desired date (1-12).
        day (int): The day of the desired date (1-31).
        hour (int): The hour of the desired time (0-23).
        minute (int): The minute of the desired time (0-59).
        second (int): The second of the desired time (0-59).

    Returns:
        list: A list containing the geocentric position of the ISS in kilometers. The list has three elements,
        representing the X, Y, and Z coordinates in a geocentric coordinate system.

    Example:
        >>> position = get_iss_position(2023, 10, 19, 12, 0, 0)
        >>> print(position)
        [909.1196049923765, 6582.567813644977, 1413.764598899465]
    """
    satellite = load_satellites(SATELLITE_NAME)

    times_scale = load.timescale()

    # You can instead use ts.now() for the current time
    time = times_scale.utc(year, month, day, hour, minute, second)

    geocentric = satellite.at(time)

    # There is no need to a nympy.ndarray, so converting to a standard python list
    return list(geocentric.position.km)
