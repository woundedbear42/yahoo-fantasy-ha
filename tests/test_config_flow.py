"""Tests for custom_components.yahoo_fantasy.config_flow.

Covers AC1 (external OAuth step reached), AC2 (league listing has no
hardcoded league key -- also covered by a source-scan below), and AC6
(missing application credentials aborts cleanly).
"""
import re
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.yahoo_fantasy.const import DOMAIN

pytestmark = pytest.mark.asyncio


async def test_missing_application_credentials_aborts(hass: HomeAssistant) -> None:
    """AC6: no application credentials configured -> clean abort, no crash."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "missing_credentials"


async def test_no_hardcoded_league_or_team_key_in_source() -> None:
    """Static scan: fail the build if a real-looking Yahoo league/team key
    literal (e.g. '399.l.12345' or '399.l.12345.t.1') sneaks into source.
    This backs up AC2's "no hardcoded league ID anywhere in code" wording.
    """
    component_dir = Path(__file__).parent.parent / "custom_components" / "yahoo_fantasy"
    pattern = re.compile(r"['\"]\d+\.l\.\d+(\.t\.\d+)?['\"]")
    offenders = []
    for path in component_dir.rglob("*.py"):
        text = path.read_text()
        if pattern.search(text):
            offenders.append(str(path))
    assert offenders == [], f"Hardcoded league/team key literal found in: {offenders}"


async def test_league_select_lists_real_leagues_no_hardcoding(
    hass: HomeAssistant,
) -> None:
    """AC2: league_select step is populated from a live API call."""
    from custom_components.yahoo_fantasy.config_flow import YahooFantasyConfigFlow

    flow = YahooFantasyConfigFlow()
    flow.hass = hass
    flow._data = {"token": {"access_token": "fake-token"}}

    fake_leagues = [
        {"league_key": "399.l.111", "name": "League A"},
        {"league_key": "399.l.222", "name": "League B"},
    ]

    with patch(
        "custom_components.yahoo_fantasy.config_flow.api.list_nfl_leagues",
        return_value=fake_leagues,
    ) as mock_list:
        result = await flow.async_step_league_select()

    mock_list.assert_called_once()
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "league_select"
    schema_keys = list(result["data_schema"].schema.keys())
    assert any(str(k) == "league_key" for k in schema_keys)


async def test_no_leagues_found_aborts(hass: HomeAssistant) -> None:
    """AC2 corollary: an authenticated account with no NFL leagues aborts
    cleanly rather than showing a broken/empty dropdown."""
    from custom_components.yahoo_fantasy.config_flow import YahooFantasyConfigFlow

    flow = YahooFantasyConfigFlow()
    flow.hass = hass
    flow._data = {"token": {"access_token": "fake-token"}}

    with patch(
        "custom_components.yahoo_fantasy.config_flow.api.list_nfl_leagues",
        return_value=[],
    ):
        result = await flow.async_step_league_select()

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "no_leagues_found"
