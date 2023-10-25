"""Tests for functions in __init__.py."""

from skyfield.api import load

from homeassistant.components.iss import (
    define_observer_information,
    define_time_range,
    get_pass_details,
)
from homeassistant.components.iss.const import (
    ALTIUDE_DEGREES,
    CET_TIMEZONE,
    OBSERVER_LATITUDE,
    OBSERVER_LONGITUDE,
)


def test_returns_get_pass_details() -> None:
    """Test for get_pass_details returns are not None."""
    skyfield_satellite_objects = load.tle_file("mock_data.txt")
    skyfield_satellite_objects_by_name = {
        sat.name: sat for sat in skyfield_satellite_objects
    }
    skyfield_satellite_object = skyfield_satellite_objects_by_name["ISS (ZARYA)"]

    observer_location, observer_timezone = define_observer_information(
        OBSERVER_LATITUDE, OBSERVER_LONGITUDE, CET_TIMEZONE
    )

    current_time, next_day_time = define_time_range()

    # Find ISS passes
    t, events = skyfield_satellite_object.find_events(
        observer_location, current_time, next_day_time, altitude_degrees=ALTIUDE_DEGREES
    )

    pass_details = get_pass_details(
        t, events, observer_timezone, observer_location, skyfield_satellite_object
    )

    assert pass_details[0]["culminate"] is not None


def test_returns_define_time_range() -> None:
    """Test for define_time_range returns are not None."""

    response = define_time_range()

    assert response[0] is not None
    assert response[1] is not None
