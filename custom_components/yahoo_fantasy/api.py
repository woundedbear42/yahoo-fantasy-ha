"""Thin synchronous wrapper around yahoo_fantasy_api for this integration.

All functions here are synchronous (yahoo_fantasy_api/requests are sync)
and are meant to be called via hass.async_add_executor_job from
config_flow.py / coordinator.py. Callers are responsible for ensuring the
YahooSession passed in carries a currently-valid bearer token.
"""
from __future__ import annotations

import logging
from typing import Any

import objectpath
from yahoo_fantasy_api import Game

from .const import GAME_CODE_NFL
from .yahoo_session import YahooSession

_LOGGER = logging.getLogger(__name__)


def list_nfl_leagues(sc: YahooSession) -> list[dict[str, str]]:
    """Return the user's current NFL leagues as [{league_key, name}, ...].

    Uses a live API call -- no hardcoded league IDs anywhere in this
    integration (spec AC2).
    """
    game = Game(sc, GAME_CODE_NFL)
    raw = game.yhandler.get_leagues_raw(game_codes=[GAME_CODE_NFL])
    tree = objectpath.Tree(raw)
    leagues: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in tree.execute("$..league"):
        if isinstance(row, dict):
            merged = row
        elif isinstance(row, list):
            merged = {}
            for item in row:
                if isinstance(item, dict):
                    merged.update(item)
        else:
            continue
        league_key = merged.get("league_key")
        name = merged.get("name")
        if league_key and name and league_key not in seen:
            seen.add(league_key)
            leagues.append({"league_key": league_key, "name": name})
    return leagues


def list_league_teams(sc: YahooSession, league_key: str) -> list[dict[str, str]]:
    """Return teams in a league the current user owns.

    Normally exactly one, but co-managed teams can yield more than one
    (spec section 4, step 4).
    """
    game = Game(sc, GAME_CODE_NFL)
    league = game.to_league(league_key)
    raw = league.yhandler.get_league_teams_raw(league_key)
    tree = objectpath.Tree(raw)
    teams: list[dict[str, str]] = []
    for row in tree.execute("$..team"):
        if not isinstance(row, list):
            continue
        merged: dict[str, Any] = {}
        for item in row:
            if isinstance(item, dict):
                merged.update(item)
        if not merged.get("team_key"):
            continue
        is_owned = merged.get("is_owned_by_current_login")
        if is_owned in (1, "1", True):
            teams.append(
                {"team_key": merged["team_key"], "name": merged.get("name", "")}
            )
    return teams


def fetch_matchup(sc: YahooSession, team_key: str) -> dict[str, Any]:
    """Fetch and parse the current-week matchup data for a team.

    Returns a dict with keys: team_score, opponent_name, opponent_score,
    week, matchup_status, record -- the exact field set from spec section 2.
    """
    game = Game(sc, GAME_CODE_NFL)
    league_key = team_key[: team_key.find(".t.")]
    league = game.to_league(league_key)
    raw = league.yhandler.get_matchup_raw(team_key, None)
    return parse_matchup(raw, team_key)


def parse_matchup(raw: dict[str, Any], team_key: str) -> dict[str, Any]:
    """Parse a Yahoo team/{key}/matchups raw JSON payload.

    Expected (abbreviated) shape:
    fantasy_content.team = [
        [ {...meta incl. team_key, name, team_standings...} ],
        {"matchups": {"0": {"matchup": {
            "week": "5",
            "status": "midevent",
            "0": {"teams": {"0": {"team": [[...], {"team_points": {...}}]},
                            "1": {"team": [[...], {"team_points": {...}}]}}}
        }}, "count": 1}},
    ]
    """
    tree = objectpath.Tree(raw)

    # Team meta (record) lives in the first element of the team array.
    meta: dict[str, Any] = {}
    for row in tree.execute("$.fantasy_content.team[0]"):
        if isinstance(row, dict):
            meta.update(row)

    record = "0-0-0"
    standings = meta.get("team_standings")
    if isinstance(standings, dict):
        totals = standings.get("outcome_totals", {})
        record = "{}-{}-{}".format(
            totals.get("wins", 0), totals.get("losses", 0), totals.get("ties", 0)
        )

    matchup = next(iter(tree.execute("$..matchup")), {})
    if not isinstance(matchup, dict):
        raise RuntimeError("Malformed matchup response: no matchup object found")

    week = int(matchup.get("week", 0))
    matchup_status = matchup.get("status", "unknown")

    teams_obj = matchup.get("0", {}).get("teams", {})
    team_score: float | None = None
    opponent_name: str | None = None
    opponent_score: float | None = None

    for key, entry in teams_obj.items():
        if key == "count":
            continue
        team_arr = entry.get("team")
        if not isinstance(team_arr, list) or len(team_arr) < 2:
            continue
        team_meta_list = team_arr[0]
        team_points = team_arr[1]

        this_meta: dict[str, Any] = {}
        for item in team_meta_list:
            if isinstance(item, dict):
                this_meta.update(item)

        points = team_points.get("team_points", {}) if isinstance(
            team_points, dict
        ) else {}
        try:
            score = float(points.get("total", 0))
        except (TypeError, ValueError):
            score = 0.0

        if this_meta.get("team_key") == team_key:
            team_score = score
        else:
            opponent_name = this_meta.get("name")
            opponent_score = score

    if team_score is None:
        raise RuntimeError("Malformed matchup response: own team not found")

    return {
        "team_score": team_score,
        "opponent_name": opponent_name or "Unknown",
        "opponent_score": opponent_score if opponent_score is not None else 0.0,
        "week": week,
        "matchup_status": matchup_status,
        "record": record,
    }
