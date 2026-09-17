"""Config flow for Yahoo Fantasy Sports.

Flow: application_credentials -> HA-native OAuth2 -> league_select ->
team_select. Unique ID = "{league_key}:{team_key}" (spec section 4).
No league/team is ever hardcoded -- league_select and team_select query
Yahoo's live API.
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow

from . import api
from .const import DOMAIN
from .yahoo_session import YahooSession

_LOGGER = logging.getLogger(__name__)


class YahooFantasyConfigFlow(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle a config flow for Yahoo Fantasy Sports."""

    DOMAIN = DOMAIN
    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        super().__init__()
        self._leagues: list[dict[str, str]] = []
        self._league_key: str | None = None
        self._league_name: str | None = None
        self._teams: list[dict[str, str]] = []

    @property
    def logger(self) -> logging.Logger:
        """Return the logger."""
        return _LOGGER

    async def async_step_creation(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """After OAuth token exchange succeeds, move to league selection."""
        # Resolve tokens first via the base implementation logic, but
        # override entry creation to insert league/team selection steps.
        try:
            token = await self.flow_impl.async_resolve_external_data(
                self.external_data
            )
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Error resolving OAuth token")
            return self.async_abort(reason="oauth_failed")

        if "expires_in" not in token:
            return self.async_abort(reason="oauth_error")

        import time

        token["expires_in"] = int(token["expires_in"])
        token["expires_at"] = time.time() + token["expires_in"]

        self._data = {
            "auth_implementation": self.flow_impl.domain,
            "token": token,
        }
        return await self.async_step_league_select()

    async def async_step_league_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """List the user's NFL leagues (live API call, no hardcoding)."""
        if user_input is not None:
            self._league_key = user_input["league_key"]
            self._league_name = next(
                (
                    league["name"]
                    for league in self._leagues
                    if league["league_key"] == self._league_key
                ),
                self._league_key,
            )
            return await self.async_step_team_select()

        sc = YahooSession(self._data["token"]["access_token"])
        try:
            self._leagues = await self.hass.async_add_executor_job(
                api.list_nfl_leagues, sc
            )
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Failed to list Yahoo NFL leagues")
            return self.async_abort(reason="cannot_connect")

        if not self._leagues:
            return self.async_abort(reason="no_leagues_found")

        return self.async_show_form(
            step_id="league_select",
            data_schema=vol.Schema(
                {
                    vol.Required("league_key"): vol.In(
                        {
                            league["league_key"]: league["name"]
                            for league in self._leagues
                        }
                    )
                }
            ),
        )

    async def async_step_team_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select which team in the league belongs to the user."""
        if user_input is not None:
            team_key = user_input["team_key"]
            team_name = next(
                (
                    team["name"]
                    for team in self._teams
                    if team["team_key"] == team_key
                ),
                team_key,
            )
            unique_id = f"{self._league_key}:{team_key}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            data = {
                **self._data,
                "league_key": self._league_key,
                "league_name": self._league_name,
                "team_key": team_key,
                "team_name": team_name,
            }
            return self.async_create_entry(
                title=f"{self._league_name} - {team_name}", data=data
            )

        sc = YahooSession(self._data["token"]["access_token"])
        try:
            self._teams = await self.hass.async_add_executor_job(
                api.list_league_teams, sc, self._league_key
            )
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Failed to list teams for league %s", self._league_key)
            return self.async_abort(reason="cannot_connect")

        if not self._teams:
            return self.async_abort(reason="no_teams_found")

        if len(self._teams) == 1:
            return await self.async_step_team_select(
                {"team_key": self._teams[0]["team_key"]}
            )

        return self.async_show_form(
            step_id="team_select",
            data_schema=vol.Schema(
                {
                    vol.Required("team_key"): vol.In(
                        {team["team_key"]: team["name"] for team in self._teams}
                    )
                }
            ),
        )
