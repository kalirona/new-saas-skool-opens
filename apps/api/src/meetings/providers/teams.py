"""
Microsoft Teams provider — requires Azure AD app with OnlineMeetings.ReadWrite.All.

Credentials: tenant_id, client_id, client_secret, user_id (set via env / config).
"""

from typing import Optional
from src.meetings.base import (
    MeetingProvider,
    MeetingProviderError,
    MeetingConfig,
    Meeting,
)


class TeamsMeetingProvider(MeetingProvider):
    @property
    def provider_name(self) -> str:
        return "teams"

    def __init__(self, config: dict):
        self.tenant_id = config.get("tenant_id", "")
        self.client_id = config.get("client_id", "")
        self.client_secret = config.get("client_secret", "")
        self.user_id = config.get("user_id", "")
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise MeetingProviderError(
                "Teams requires tenant_id, client_id, and client_secret. "
                "Set LEARNHOUSE_TEAMS_TENANT_ID, LEARNHOUSE_TEAMS_CLIENT_ID, "
                "LEARNHOUSE_TEAMS_CLIENT_SECRET in environment.",
                provider="teams",
                code="missing_credentials",
            )

    async def _get_access_token(self) -> str:
        import httpx
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data=data)
            resp.raise_for_status()
            return resp.json()["access_token"]

    async def create_meeting(self, config: MeetingConfig) -> Meeting:
        token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "subject": config.title,
            "startDateTime": config.start_time,
            "endDateTime": config.end_time,
            "participants": {
                "organizer": {
                    "identity": {
                        "user": {
                            "id": self.user_id,
                        }
                    }
                }
            },
        }
        if config.duration_minutes and config.start_time:
            from datetime import datetime, timedelta
            try:
                start = datetime.fromisoformat(config.start_time)
                payload["endDateTime"] = (start + timedelta(minutes=config.duration_minutes)).isoformat()
            except (ValueError, TypeError):
                pass

        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://graph.microsoft.com/v1.0/users/{self.user_id}/onlineMeetings",
                json=payload,
                headers=headers,
            )
            if resp.status_code in (401, 403):
                raise MeetingProviderError(
                    "Teams API authentication failed. Check credentials.",
                    provider="teams", code="auth_failed",
                )
            resp.raise_for_status()
            data = resp.json()
            return Meeting(
                provider_meeting_id=data.get("id", ""),
                join_url=data.get("joinUrl", ""),
            )

    async def update_meeting(
        self, provider_meeting_id: str, config: MeetingConfig
    ) -> Meeting:
        token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {"subject": config.title}
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"https://graph.microsoft.com/v1.0/users/{self.user_id}/onlineMeetings/{provider_meeting_id}",
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
                f"https://graph.microsoft.com/v1.0/users/{self.user_id}/onlineMeetings/{provider_meeting_id}",
                headers=headers,
            )
            resp.raise_for_status()

    async def get_meeting(self, provider_meeting_id: str) -> Optional[Meeting]:
        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://graph.microsoft.com/v1.0/users/{self.user_id}/onlineMeetings/{provider_meeting_id}",
                headers=headers,
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
            return Meeting(
                provider_meeting_id=data.get("id", ""),
                join_url=data.get("joinUrl", ""),
            )
