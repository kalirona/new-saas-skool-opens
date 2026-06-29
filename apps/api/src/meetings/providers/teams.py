"""
Microsoft Teams provider — architecture / stub.

Requires a Microsoft Entra ID (Azure AD) app with the
OnlineMeetings.ReadWrite.All permission and an OAuth2 client
credentials flow.

Steps to complete:
  1. Register an app in Azure AD → Certificates & secrets.
  2. Add API permission: OnlineMeetings.ReadWrite.All (Application).
  3. Grant admin consent.
  4. Use Microsoft Graph API:
     POST /v1.0/users/{user_id}/onlineMeetings
  5. Response includes joinUrl, conferenceId, and meetingId.
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

    async def _get_access_token(self) -> str:
        raise NotImplementedError(
            "Microsoft Teams requires an Azure AD app registration.\n"
            "1. Register an app in https://portal.azure.com.\n"
            "2. Add OnlineMeetings.ReadWrite.All permission.\n"
            "3. Set LEARNHOUSE_TEAMS_TENANT_ID, LEARNHOUSE_TEAMS_CLIENT_ID,\n"
            "   LEARNHOUSE_TEAMS_CLIENT_SECRET in environment.\n"
            "4. Implement OAuth2 client credentials grant."
        )

    async def create_meeting(self, config: MeetingConfig) -> Meeting:
        raise NotImplementedError(
            "Teams meeting creation requires Azure AD credentials."
        )

    async def update_meeting(
        self, provider_meeting_id: str, config: MeetingConfig
    ) -> Meeting:
        raise NotImplementedError("Teams provider not fully implemented")

    async def delete_meeting(self, provider_meeting_id: str) -> None:
        raise NotImplementedError("Teams provider not fully implemented")

    async def get_meeting(self, provider_meeting_id: str) -> Optional[Meeting]:
        raise NotImplementedError("Teams provider not fully implemented")
