"""
Zoom Meeting provider — architecture / stub.

Requires a Zoom Server-to-Server OAuth app and the zoom_us
package (or direct REST API calls) to be fully implemented.

Steps to complete:
  1. Add zoom_us (or httpx) to dependencies.
  2. Implement OAuth2 token refresh with account_id / client_id / client_secret.
  3. Call POST /v2/users/me/meetings to create meetings.
  4. Handle webhook events from Zoom Marketplace.
"""

from typing import Optional
from src.meetings.base import (
    MeetingProvider,
    MeetingProviderError,
    MeetingConfig,
    Meeting,
)


class ZoomMeetingProvider(MeetingProvider):
    @property
    def provider_name(self) -> str:
        return "zoom"

    def __init__(self, config: dict):
        self.account_id = config.get("account_id", "")
        self.client_id = config.get("client_id", "")
        self.client_secret = config.get("client_secret", "")
        self.webhook_secret = config.get("webhook_secret", "")

    async def _get_access_token(self) -> str:
        raise NotImplementedError(
            "Zoom provider requires a Zoom Server-to-Server OAuth app.\n"
            "1. Create an app at https://marketplace.zoom.us/develop/create\n"
            "2. Set LEARNHOUSE_ZOOM_ACCOUNT_ID, LEARNHOUSE_ZOOM_CLIENT_ID, "
            "LEARNHOUSE_ZOOM_CLIENT_SECRET in environment.\n"
            "3. Implement OAuth2 token exchange here using httpx."
        )

    async def create_meeting(self, config: MeetingConfig) -> Meeting:
        raise NotImplementedError(
            "Zoom meeting creation requires a Zoom API key. "
            "See ZoomMeetingProvider docstring for setup instructions."
        )

    async def update_meeting(
        self, provider_meeting_id: str, config: MeetingConfig
    ) -> Meeting:
        raise NotImplementedError("Zoom provider not fully implemented")

    async def delete_meeting(self, provider_meeting_id: str) -> None:
        raise NotImplementedError("Zoom provider not fully implemented")

    async def get_meeting(self, provider_meeting_id: str) -> Optional[Meeting]:
        raise NotImplementedError("Zoom provider not fully implemented")

    async def handle_webhook(
        self, raw_body: bytes, signature_header: Optional[str] = None
    ):
        raise NotImplementedError("Zoom webhook handling not implemented")
