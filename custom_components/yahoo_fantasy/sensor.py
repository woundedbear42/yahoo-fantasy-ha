"""Sensor platform for Yahoo Fantasy Sports.

Exposes one sensor per config entry: state = current-week team score,
attributes = opponent_name/opponent_score/week/matchup_status/record
(spec section 2 / AC3). Never exposes tokens/secrets in attributes
(spec AC7).
"""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LEAGUE_KEY, CONF_TEAM_KEY, CONF_TEAM_NAME, DOMAIN
from .coordinator import YahooFantasyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Yahoo Fantasy sensor from a config entry."""
    coordinator: YahooFantasyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([YahooFantasyMatchupSensor(coordinator, entry)])


class YahooFantasyMatchupSensor(CoordinatorEntity[YahooFantasyCoordinator], SensorEntity):
    """Sensor exposing the current-week matchup for one Yahoo fantasy team."""

    _attr_has_entity_name = True
    _attr_name = "Matchup"
    _attr_native_unit_of_measurement = "pts"

    def __init__(
        self, coordinator: YahooFantasyCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        team_key = entry.data[CONF_TEAM_KEY]
        league_key = entry.data[CONF_LEAGUE_KEY]
        self._attr_unique_id = f"{league_key}:{team_key}_matchup"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{league_key}:{team_key}")},
            name=entry.data.get(CONF_TEAM_NAME, team_key),
            manufacturer="Yahoo Fantasy Sports",
        )

    @property
    def native_value(self) -> float | None:
        """Return the team's current-week fantasy points."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("team_score")

    @property
    def extra_state_attributes(self) -> dict:
        """Return matchup attributes. Never includes tokens/secrets."""
        data = self.coordinator.data or {}
        return {
            "opponent_name": data.get("opponent_name"),
            "opponent_score": data.get("opponent_score"),
            "week": data.get("week"),
            "matchup_status": data.get("matchup_status"),
            "record": data.get("record"),
        }
