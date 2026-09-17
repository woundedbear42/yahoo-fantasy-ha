"""Tests for custom_components.yahoo_fantasy.sensor.

Covers AC3 (state = team_score, attributes = the exact required field set)
and AC7's "no secrets in attributes" guarantee.
"""
from unittest.mock import MagicMock

import pytest

from custom_components.yahoo_fantasy.const import (
    CONF_LEAGUE_KEY,
    CONF_TEAM_KEY,
    CONF_TEAM_NAME,
)
from custom_components.yahoo_fantasy.sensor import YahooFantasyMatchupSensor

pytestmark = pytest.mark.asyncio


def _make_entry():
    entry = MagicMock()
    entry.data = {
        CONF_LEAGUE_KEY: "399.l.1",
        CONF_TEAM_KEY: "399.l.1.t.1",
        CONF_TEAM_NAME: "My Team",
        "token": {"access_token": "should-never-appear-in-attributes"},
    }
    entry.entry_id = "test_entry"
    return entry


def _make_coordinator(data):
    coordinator = MagicMock()
    coordinator.data = data
    coordinator.last_update_success = True
    return coordinator


async def test_sensor_state_is_team_score() -> None:
    entry = _make_entry()
    coordinator = _make_coordinator(
        {
            "team_score": 123.4,
            "opponent_name": "Rival",
            "opponent_score": 100.0,
            "week": 3,
            "matchup_status": "midevent",
            "record": "5-2-0",
        }
    )

    sensor = YahooFantasyMatchupSensor(coordinator, entry)

    assert sensor.native_value == 123.4


async def test_sensor_attributes_match_required_field_set() -> None:
    entry = _make_entry()
    coordinator = _make_coordinator(
        {
            "team_score": 123.4,
            "opponent_name": "Rival",
            "opponent_score": 100.0,
            "week": 3,
            "matchup_status": "midevent",
            "record": "5-2-0",
        }
    )

    sensor = YahooFantasyMatchupSensor(coordinator, entry)
    attrs = sensor.extra_state_attributes

    assert attrs == {
        "opponent_name": "Rival",
        "opponent_score": 100.0,
        "week": 3,
        "matchup_status": "midevent",
        "record": "5-2-0",
    }


async def test_sensor_never_exposes_secrets_in_attributes() -> None:
    """AC7: grep-equivalent check that attributes never contain the token."""
    entry = _make_entry()
    coordinator = _make_coordinator(
        {
            "team_score": 1.0,
            "opponent_name": "Rival",
            "opponent_score": 1.0,
            "week": 1,
            "matchup_status": "preevent",
            "record": "0-0-0",
        }
    )

    sensor = YahooFantasyMatchupSensor(coordinator, entry)
    attrs = sensor.extra_state_attributes

    serialized = str(attrs)
    assert "should-never-appear-in-attributes" not in serialized
    assert "token" not in serialized.lower()
    assert "secret" not in serialized.lower()


async def test_sensor_handles_no_coordinator_data_gracefully() -> None:
    """When the coordinator has no data yet (before first refresh), the
    sensor must not raise -- state is None, attributes are empty-ish."""
    entry = _make_entry()
    coordinator = _make_coordinator(None)

    sensor = YahooFantasyMatchupSensor(coordinator, entry)

    assert sensor.native_value is None
    attrs = sensor.extra_state_attributes
    assert attrs["opponent_name"] is None
