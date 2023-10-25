"""Tests for functions in __init__.py."""

from datetime import datetime

from skyfield.api import load
from skyfield.timelib import Time

from homeassistant.components.iss import (
    define_observer_information,
    define_time_range,
    get_pass_details,
    select_satellite,
)
from homeassistant.components.iss.const import (
    ALTIUDE_DEGREES,
    CET_TIMEZONE,
    OBSERVER_LATITUDE,
    OBSERVER_LONGITUDE,
)


def test_get_pass_details() -> None:
    """Test for get_pass_details."""
    skyfield_satellite_objects = load.tle_file("mock_data.txt")
    skyfield_satellite_objects_by_name = {
        sat.name: sat for sat in skyfield_satellite_objects
    }
    skyfield_satellite_object = skyfield_satellite_objects_by_name["ISS (ZARYA)"]

    observer_location, observer_timezone = define_observer_information(
        OBSERVER_LATITUDE, OBSERVER_LONGITUDE, CET_TIMEZONE
    )

    # Get the current time
    now = datetime(2023, 10, 25, 14, 30, 0)

    current_time, next_day_time = define_time_range(now)

    # Find ISS passes
    t, events = skyfield_satellite_object.find_events(
        observer_location, current_time, next_day_time, altitude_degrees=ALTIUDE_DEGREES
    )

    pass_details = get_pass_details(
        t, events, observer_timezone, observer_location, skyfield_satellite_object
    )

    assert isinstance(pass_details, list)
    assert len(pass_details) == 5
    assert pass_details[0]["culminate"]["Datetime"] == "2023 Oct 25 17:31:35"
    assert pass_details[0]["culminate"]["Azimuth"] == 218.8354077873246
    assert pass_details[0]["culminate"]["Altitude"] == 69.85713951881213


def test_define_time_range() -> None:
    """Test for define_time_range."""

    # Get the current time
    now = datetime(2023, 10, 25, 14, 30, 0)

    # Calculate the expected next day's end time
    local_timescale = load.timescale()
    expected_start_time = local_timescale.utc(2023, 10, 25, 14, 30, 0)
    expected_end_time = local_timescale.utc(2023, 10, 26, 23, 59, 59)

    # Call the function
    start_time, end_time = define_time_range(now)

    # Check that the start_time is correct
    assert start_time == expected_start_time

    # Check that the end_time is correct
    assert end_time == expected_end_time

    # Check that start_time is before end_time
    assert float(str(start_time).split("=")[1].split(">")[0]) < float(
        str(end_time).split("=")[1].split(">")[0]
    )

    # Check that the types are correct
    assert isinstance(start_time, Time)
    assert isinstance(end_time, Time)


def test_load_satellites() -> None:
    """Test for the loading of satellites available in the API."""

    satellites = load.tle_file("mock_data.txt")

    satellite = select_satellite(satellites, "ISS (ZARYA)")

    assert "ISS (ZARYA) catalog #25544" in str(satellite)
