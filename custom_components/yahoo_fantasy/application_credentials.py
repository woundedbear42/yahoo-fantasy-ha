"""Application credentials platform for Yahoo Fantasy Sports.

Declares Yahoo's OAuth2 authorize/token endpoints so this integration can
use Home Assistant's native config_entry_oauth2_flow. This intentionally
does NOT use yahoo_oauth's file-based OAuth2(from_file=...) flow -- HA owns
token storage/refresh via the config entry (see spec section 3).
"""
from homeassistant.components.application_credentials import (
    AuthorizationServer,
)
from homeassistant.core import HomeAssistant

from .const import OAUTH2_AUTHORIZE, OAUTH2_TOKEN


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Return the Yahoo OAuth2 authorization server endpoints."""
    return AuthorizationServer(
        authorize_url=OAUTH2_AUTHORIZE,
        token_url=OAUTH2_TOKEN,
    )
