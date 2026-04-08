"""
In-memory session store for the Translation API.

Stores per-channel state:
  - language: "hindi" or "gujarati"
  - access_token: JWT from fastworkflow /initialize
  - refresh_token: JWT refresh token from fastworkflow /initialize
"""

import threading
from typing import Optional


class SessionStore:
    """Thread-safe in-memory store mapping channel_id → session state."""

    def __init__(self):
        self._store: dict[str, dict] = {}
        self._lock = threading.Lock()

    def set_session(
        self,
        channel_id: str,
        language: str,
        access_token: str,
        refresh_token: str,
    ) -> None:
        """Create or update a session for a channel."""
        with self._lock:
            self._store[channel_id] = {
                "language": language,
                "access_token": access_token,
                "refresh_token": refresh_token,
            }

    def get_session(self, channel_id: str) -> Optional[dict]:
        """Return session dict or None if not found."""
        with self._lock:
            return self._store.get(channel_id)

    def get_language(self, channel_id: str) -> Optional[str]:
        """Return language for channel, or None."""
        session = self.get_session(channel_id)
        return session["language"] if session else None

    def get_access_token(self, channel_id: str) -> Optional[str]:
        """Return stored JWT access token for channel, or None."""
        session = self.get_session(channel_id)
        return session["access_token"] if session else None

    def update_tokens(
        self, channel_id: str, access_token: str, refresh_token: str
    ) -> None:
        """Update JWT tokens for an existing session (e.g. after refresh)."""
        with self._lock:
            if channel_id in self._store:
                self._store[channel_id]["access_token"] = access_token
                self._store[channel_id]["refresh_token"] = refresh_token

    def delete_session(self, channel_id: str) -> None:
        """Remove a session."""
        with self._lock:
            self._store.pop(channel_id, None)

    def has_session(self, channel_id: str) -> bool:
        """Check if a session exists for the channel."""
        with self._lock:
            return channel_id in self._store


# Module-level singleton
store = SessionStore()
