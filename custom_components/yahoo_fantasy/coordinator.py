"""DataUpdateCoordinator for Yahoo Fantasy Sports.

Fixed 15-minute polling interval (spec section 5, AC4). Degrades to
UpdateFailed on Yahoo API errors / malformed responses rather than
crashing HA's update loop (spec non-functional requirement: reliability).
Never logs tokens -- only league_key/week context on failure (spec
non-functional requirement: observability, AC7).
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import api
from .const import CONF_LEAGUE_KEY, CONF_TEAM_KEY, DOMAIN, UPDATE_INTERVAL
from .yahoo_session import YahooSession

_LOGGER = logging.getLogger(__name__)


class YahooFantasyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls Yahoo Fantasy Sports for one team's matchup."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.data[CONF_TEAM_KEY]}",
            update_interval=UPDATE_INTERVAL,
        )
        self.entry = entry
        self.oauth_session = oauth_session
        self.league_key = entry.data[CONF_LEAGUE_KEY]
        self.team_key = entry.data[CONF_TEAM_KEY]

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest matchup data for the configured team."""
        try:
            await self.oauth_session.async_ensure_token_valid()
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Token refresh failed for league %s: %s", self.league_key, err
            )
            raise UpdateFailed("Token refresh failed") from err

        access_token = self.oauth_session.token["access_token"]
        sc = YahooSession(access_token)

        try:
            return await self.hass.async_add_executor_job(
                api.fetch_matchup, sc, self.team_key
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Failed to fetch matchup for league %s: %s", self.league_key, err
            )
            raise UpdateFailed(f"Error communicating with Yahoo API: {err}") from err
