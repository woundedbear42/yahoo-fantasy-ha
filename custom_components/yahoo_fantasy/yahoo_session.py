"""Adapter bridging HA's OAuth2Session onto a requests.Session-like object.

yahoo_fantasy_api's query classes (Game/League/Team) expect a session
context object `sc` with a `.session` attribute exposing requests.Session's
get/put/post methods. HA owns the OAuth2 token lifecycle via
config_entry_oauth2_flow.OAuth2Session; this adapter injects the current
bearer token into a plain requests.Session so those sync calls (which we
run in an executor) carry a valid Authorization header.

This intentionally never touches yahoo_oauth's file-based OAuth2 flow --
tokens live only in the HA config entry.
"""
from __future__ import annotations

import requests


class YahooSession:
    """A requests.Session-like object carrying an HA-managed bearer token."""

    def __init__(self, access_token: str) -> None:
        """Initialize with the current valid access token."""
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {access_token}"}
        )

    def refresh_access_token(self) -> dict:
        """Not used: HA's OAuth2Session refreshes tokens, not yahoo_fantasy_api.

        yhandler.YHandler checks hasattr(self.sc, 'refresh_access_token')
        only as a fallback when it gets a 401 mid-request. Since the
        coordinator always calls OAuth2Session.async_ensure_token_valid()
        immediately before building a YahooSession, a mid-request 401
        should not normally occur. We intentionally do not implement
        transparent token refresh here to avoid a second, uncoordinated
        refresh path racing with HA's own token storage.
        """
        raise RuntimeError(
            "YahooSession does not support in-band token refresh; "
            "token validity must be ensured before use."
        )
