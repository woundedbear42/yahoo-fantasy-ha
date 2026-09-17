"""Tests for custom_components.yahoo_fantasy.api (parsing logic, mocked API)."""
from unittest.mock import MagicMock

from custom_components.yahoo_fantasy import api


def _matchup_raw(team_key="399.l.1.t.1", opp_key="399.l.1.t.2"):
    return {
        "fantasy_content": {
            "team": [
                [
                    {"team_key": team_key},
                    {"name": "My Team"},
                    {
                        "team_standings": {
                            "outcome_totals": {
                                "wins": "7",
                                "losses": "4",
                                "ties": "0",
                            }
                        }
                    },
                ],
                {
                    "matchups": {
                        "0": {
                            "matchup": {
                                "week": "5",
                                "status": "midevent",
                                "0": {
                                    "teams": {
                                        "0": {
                                            "team": [
                                                [{"team_key": team_key}, {"name": "My Team"}],
                                                {"team_points": {"total": "88.5"}},
                                            ]
                                        },
                                        "1": {
                                            "team": [
                                                [{"team_key": opp_key}, {"name": "Rival Squad"}],
                                                {"team_points": {"total": "75.25"}},
                                            ]
                                        },
                                        "count": 2,
                                    }
                                },
                            }
                        },
                        "count": 1,
                    }
                },
            ]
        }
    }


def test_parse_matchup_returns_expected_fields():
    team_key = "399.l.1.t.1"
    raw = _matchup_raw(team_key=team_key)

    result = api.parse_matchup(raw, team_key)

    assert result["team_score"] == 88.5
    assert result["opponent_name"] == "Rival Squad"
    assert result["opponent_score"] == 75.25
    assert result["week"] == 5
    assert result["matchup_status"] == "midevent"
    assert result["record"] == "7-4-0"


def test_parse_matchup_raises_on_missing_own_team():
    raw = _matchup_raw(team_key="399.l.1.t.1")

    # Ask for a team key that doesn't appear in the payload.
    try:
        api.parse_matchup(raw, "399.l.1.t.99")
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


def test_list_nfl_leagues_no_hardcoded_league_key(monkeypatch):
    """AC2: league listing must come from a live API call, never a constant."""
    raw = {
        "fantasy_content": {
            "users": {
                "0": {
                    "user": [
                        {},
                        {
                            "games": {
                                "0": {
                                    "game": [
                                        {},
                                        {
                                            "leagues": {
                                                "0": {
                                                    "league": [
                                                        {
                                                            "league_key": "399.l.12345",
                                                            "name": "My League",
                                                        }
                                                    ]
                                                },
                                                "count": 1,
                                            }
                                        },
                                    ]
                                }
                            }
                        },
                    ]
                }
            }
        }
    }

    mock_sc = MagicMock()
    fake_game = MagicMock()
    fake_game.yhandler.get_leagues_raw.return_value = raw
    monkeypatch.setattr(api, "Game", lambda sc, code: fake_game)

    leagues = api.list_nfl_leagues(mock_sc)

    assert leagues == [{"league_key": "399.l.12345", "name": "My League"}]
    fake_game.yhandler.get_leagues_raw.assert_called_once()
