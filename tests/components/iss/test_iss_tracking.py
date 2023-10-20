"""Test for ISS tracking."""


from skyfield.api import load

from homeassistant.components.iss.iss_tracking import get_iss_position, select_satellite


def test_load_satellites() -> None:
    """Test for the loading of satellites available in the API."""

    satellites = load.tle_file("mock_data.txt")

    satellite = select_satellite(satellites, "ISS (ZARYA)")

    assert "ISS (ZARYA) catalog #25544" in str(satellite)


def test_get_iss_position() -> None:
    """Test the position API with two known values."""

    satellites = load.tle_file("mock_data.txt")

    by_name = {sat.name: sat for sat in satellites}

    satellite = by_name["ISS (ZARYA)"]

    assert get_iss_position(2023, 10, 23, 23, 59, 0, satellite) == [
        4446.450776093347,
        -904.8707020713027,
        -5066.276628282272,
    ]
