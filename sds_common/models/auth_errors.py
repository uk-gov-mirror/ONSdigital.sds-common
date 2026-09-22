from __future__ import annotations
class SdsAuthError(Exception):
    """Base class for authentication and secret-management errors."""


class SecretAccessError(SdsAuthError):
    """Raised when a secret version cannot be accessed from Google Cloud Secret Manager."""

    def __init__(self, error_detail: str) -> None:
        self.error_detail = error_detail
        super().__init__(
            f"Failed to access secret version from Google Cloud Secret Manager: {error_detail}"
        )


class SecretKeyError(SdsAuthError):
    """Raised when the OAuth client ID key is absent from the retrieved secret payload."""

    def __init__(self) -> None:
        super().__init__("OAuth client ID not found in secret.")
