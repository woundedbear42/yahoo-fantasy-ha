# Yahoo Fantasy HA

Home Assistant custom_component exposing Yahoo Fantasy NFL score/matchup data
(current week team score, opponent name/score, season record, week number,
matchup status) as a sensor entity, per league/team.

## Installation (HACS custom repository)

1. In Home Assistant, open HACS > Integrations > the "..." menu (top right)
   > Custom repositories.
2. Add `https://github.com/woundedbear42/yahoo-fantasy-ha` with category
   "Integration".
3. Find "Yahoo Fantasy Sports" in HACS and install it, then restart Home
   Assistant.

## Prerequisite: create a Yahoo Developer Network application

This is a manual step you must do once, before setup, and cannot be
automated:

1. Go to https://developer.yahoo.com/apps/create/ (sign in with the Yahoo
   account that owns the fantasy team).
2. Application Name: any descriptive name (e.g. "Home Assistant Fantasy
   Sensor").
3. Application Type: "Web Application" (Confidential Client) — a redirect
   URI is required.
4. Redirect URI: `https://<your-ha-url>/auth/external/callback` — your HA
   instance must be reachable at that HTTPS URL for the OAuth step to
   complete.
5. API Permissions: check "Fantasy Sports" — Read access is sufficient
   (this is a read-only integration).
6. Create the app; copy the Client ID (Consumer Key) and Client Secret
   (Consumer Secret) immediately — the secret is not re-displayed later.

## Setup

1. In Home Assistant, go to Settings > Devices & Services > Application
   Credentials and add a new entry for the `yahoo_fantasy` domain using the
   Client ID/Secret from above.
2. Go to Settings > Devices & Services > Add Integration > "Yahoo Fantasy
   Sports". You will be redirected to Yahoo to authorize access, then asked
   to select your NFL league and team (both populated live from your Yahoo
   account — nothing is hardcoded).
3. A `sensor.<team>_matchup` entity is created, polling every 15 minutes.
   State = current-week fantasy points; attributes = `opponent_name`,
   `opponent_score`, `week`, `matchup_status`, `record`.

## Development

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-test.txt
pytest tests/ -v
```

See the kanban board for the full spec and acceptance criteria.
