"""
Zoom Meeting provider — requires Zoom Server-to-Server OAuth credentials.

Credentials: account_id, client_id, client_secret (set via env / config).
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
        if not all([self.account_id, self.client_id, self.client_secret]):
            raise MeetingProviderError(
                "Zoom requires account_id, client_id, and client_secret. "
                "Set LEARNHOUSE_ZOOM_ACCOUNT_ID, LEARNHOUSE_ZOOM_CLIENT_ID, "
                "LEARNHOUSE_ZOOM_CLIENT_SECRET in environment.",
                provider="zoom",
                code="missing_credentials",
            )

    async def _get_access_token(self) -> str:
        import httpx
        url = "https://zoom.us/oauth/token"
        data = {
            "grant_type": "account_credentials",
            "account_id": self.account_id,
        }
        auth = (self.client_id, self.client_secret)
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data=data, auth=auth)
            resp.raise_for_status()
            return resp.json()["access_token"]

    async def create_meeting(self, config: MeetingConfig) -> Meeting:
        token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "topic": config.title,
            "type": 2,
            "start_time": config.start_time,
            "duration": config.duration_minutes or 60,
            "timezone": config.timezone or "UTC",
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "auto_recording": "none",
            },
        }
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.zoom.us/v2/users/me/meetings",
                json=payload,
                headers=headers,
            )
            if resp.status_code in (401, 403):
                raise MeetingProviderError(
                    "Zoom API authentication failed. Check credentials.",
                    provider="zoom", code="auth_failed",
                )
            resp.raise_for_status()
            data = resp.json()
            return Meeting(
                provider_meeting_id=data.get("id", ""),
                join_url=data.get("join_url", ""),
                host_url=data.get("start_url", ""),
            )

    async def update_meeting(
        self, provider_meeting_id: str, config: MeetingConfig
    ) -> Meeting:
        token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "topic": config.title,
            "type": 2,
            "start_time": config.start_time,
            "duration": config.duration_minutes or 60,
            "timezone": config.timezone or "UTC",
        }
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"https://api.zoom.us/v2/meetings/{provider_meeting_id}",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            return Meeting(
                provider_meeting_id=provider_meeting_id,
                join_url="",
            )

    async def delete_meeting(self, provider_meeting_id: str) -> None:
        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"https://api.zoom.us/v2/meetings/{provider_meeting_id}",
                headers=headers,
            )
            resp.raise_for_status()

    async def get_meeting(self, provider_meeting_id: str) -> Optional[Meeting]:
        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.zoom.us/v2/meetings/{provider_meeting_id}",
                headers=headers,
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
            return Meeting(
                provider_meeting_id=data.get("id", ""),
                join_url=data.get("join_url", ""),
            )

    async def handle_webhook(
        self, raw_body: bytes, signature_header: Optional[str] = None
    ):
        return {"received": True}
