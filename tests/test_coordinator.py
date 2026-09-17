"""Tests for custom_components.yahoo_fantasy.coordinator.

Covers AC4 (fixed 15-minute interval) and the reliability requirement
that API/malformed-response errors degrade to UpdateFailed rather than
raising into HA's update loop.
"""
import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.yahoo_fantasy.const import (
    CONF_LEAGUE_KEY,
    CONF_TEAM_KEY,
    UPDATE_INTERVAL,
)
from custom_components.yahoo_fantasy.coordinator import YahooFantasyCoordinator

pytestmark = pytest.mark.asyncio


def _make_entry():
    entry = MagicMock()
    entry.data = {
        CONF_LEAGUE_KEY: "399.l.1",
        CONF_TEAM_KEY: "399.l.1.t.1",
    }
    entry.entry_id = "test_entry"
    return entry


async def test_update_interval_is_fixed_15_minutes(hass) -> None:
    """AC4: coordinator polls on a fixed 15-minute interval."""
    entry = _make_entry()
    oauth_session = AsyncMock()
    oauth_session.token = {"access_token": "fake"}

    coordinator = YahooFantasyCoordinator(hass, entry, oauth_session)

    assert coordinator.update_interval == datetime.timedelta(minutes=15)
    assert UPDATE_INTERVAL == datetime.timedelta(minutes=15)


async def test_update_returns_expected_data_shape(hass) -> None:
    """Coordinator refresh returns the exact field set sensor.py expects."""
    entry = _make_entry()
    oauth_session = AsyncMock()
    oauth_session.token = {"access_token": "fake"}

    coordinator = YahooFantasyCoordinator(hass, entry, oauth_session)

    fake_result = {
        "team_score": 100.0,
        "opponent_name": "Rival",
        "opponent_score": 90.0,
        "week": 6,
        "matchup_status": "postevent",
        "record": "8-4-0",
    }
    with patch(
        "custom_components.yahoo_fantasy.coordinator.api.fetch_matchup",
        return_value=fake_result,
    ):
        data = await coordinator._async_update_data()

    assert data == fake_result
    oauth_session.async_ensure_token_valid.assert_awaited_once()


async def test_update_degrades_to_update_failed_on_api_error(hass) -> None:
    """Reliability: Yahoo API errors must raise UpdateFailed, not propagate."""
    entry = _make_entry()
    oauth_session = AsyncMock()
    oauth_session.token = {"access_token": "fake"}

    coordinator = YahooFantasyCoordinator(hass, entry, oauth_session)

    with patch(
        "custom_components.yahoo_fantasy.coordinator.api.fetch_matchup",
        side_effect=RuntimeError("Yahoo 500"),
    ):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


async def test_update_degrades_to_update_failed_on_token_refresh_error(hass) -> None:
    """Reliability: a token-refresh failure also degrades to UpdateFailed."""
    entry = _make_entry()
    oauth_session = AsyncMock()
    oauth_session.async_ensure_token_valid.side_effect = RuntimeError("refresh failed")
    oauth_session.token = {"access_token": "fake"}

    coordinator = YahooFantasyCoordinator(hass, entry, oauth_session)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
