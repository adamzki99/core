"""Test for ISS tracking."""

from homeassistant.components.iss.iss_tracking import get_iss_position, load_satellites


def test_load_satellites() -> None:
    """Test for the loading of satellites available in the API."""

    assert "ISS (ZARYA)" in str(load_satellites("ISS (ZARYA)"))


def test_get_iss_position() -> None:
    """Test the position API with two known values."""

    assert get_iss_position(2023, 10, 19, 12, 0, 0) == [
        909.1196049923765,
        6582.567813644977,
        1413.764598899465,
    ]

    assert get_iss_position(2022, 12, 26, 1, 4, 12) == [
        -1817.191585681201,
        -5993.559286151532,
        2698.683674033191,
    ]
