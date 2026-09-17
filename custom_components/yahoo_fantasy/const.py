"""Constants for the Yahoo Fantasy Sports integration."""
from datetime import timedelta

DOMAIN = "yahoo_fantasy"

OAUTH2_AUTHORIZE = "https://api.login.yahoo.com/oauth2/request_auth"
OAUTH2_TOKEN = "https://api.login.yahoo.com/oauth2/get_token"

API_BASE_URL = "https://fantasysports.yahooapis.com/fantasy/v2"

# Fixed 15-minute polling interval per spec section 5. Not user-configurable
# in v1 (see spec section 4, "Options flow: none required for v1").
UPDATE_INTERVAL = timedelta(minutes=15)

CONF_LEAGUE_KEY = "league_key"
CONF_LEAGUE_NAME = "league_name"
CONF_TEAM_KEY = "team_key"
CONF_TEAM_NAME = "team_name"

GAME_CODE_NFL = "nfl"

MATCHUP_STATUS_PREEVENT = "preevent"
MATCHUP_STATUS_MIDEVENT = "midevent"
MATCHUP_STATUS_POSTEVENT = "postevent"
