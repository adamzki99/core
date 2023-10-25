"""Support for iss sensor."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, CONF_SHOW_ON_MAP
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import IssData
from .const import DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: DataUpdateCoordinator[IssData] = hass.data[DOMAIN]

    show_on_map = entry.options.get(CONF_SHOW_ON_MAP, False)

    async_add_entities(
        [
            IssSensor(coordinator, entry, show_on_map, "people"),
            IssSensor(coordinator, entry, show_on_map, "pass_time"),
            IssSensor(coordinator, entry, show_on_map, "pass_azimuth"),
            IssSensor(coordinator, entry, show_on_map, "pass_altitude"),
        ]
    )


class IssSensor(CoordinatorEntity[DataUpdateCoordinator[IssData]], SensorEntity):
    """Implementation of the ISS sensor."""

    _attr_has_entity_name = True
    _attr_name = None
    _key: str

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[IssData],
        entry: ConfigEntry,
        show: bool,
        key: str,
    ) -> None:
        """Initialize the sensor."""
        self._key = key
        super().__init__(coordinator)
        self.entity_id = f"sensor.iss_{key}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._show_on_map = show
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=DEFAULT_NAME,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self):
        """Return number of people in space."""
        if self._key == "people":
            return self.coordinator.data.number_of_people_in_space
        if self._key == "pass_azimuth":
            return self.coordinator.data.iss_passes.get("Azimuth")
        if self._key == "pass_altitude":
            return self.coordinator.data.iss_passes.get("Altitude")
        return self.coordinator.data.iss_passes.get("Datetime")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {}
        if self._show_on_map and self._key == "pass_time":
            attrs[ATTR_LONGITUDE] = self.coordinator.data.current_location.get(
                "longitude"
            )
            attrs[ATTR_LATITUDE] = self.coordinator.data.current_location.get(
                "latitude"
            )
            attrs["pass_time"] = self.coordinator.data.iss_passes.get("Datetime")
            attrs["pass_azimuth"] = self.coordinator.data.iss_passes.get("Azimuth")
            attrs["pass_altitude"] = self.coordinator.data.iss_passes.get("Altitude")

            attrs["pass_time"] = self.coordinator.data.iss_passes.get("Datetime")
            attrs["pass_azimuth"] = self.coordinator.data.iss_passes.get("Azimuth")
            attrs["pass_altitude"] = self.coordinator.data.iss_passes.get("Altitude")

        else:
            attrs["long"] = self.coordinator.data.current_location.get("longitude")
            attrs["lat"] = self.coordinator.data.current_location.get("latitude")

        return attrs
