"""
Custom URL meeting provider.

Simply stores and returns a user-provided URL.
No API integration required.
"""

from typing import Optional
from src.meetings.base import MeetingProvider, MeetingProviderError, MeetingConfig, Meeting


class CustomUrlMeetingProvider(MeetingProvider):
    @property
    def provider_name(self) -> str:
        return "custom_url"

    def __init__(self, config: dict):
        self.allowed_domains = config.get("allowed_domains", [])

    async def create_meeting(self, config: MeetingConfig) -> Meeting:
        join_url = config.settings.get("join_url", "")
        if not join_url:
            raise MeetingProviderError(
                "join_url is required for custom URL meetings",
                provider="custom_url",
                code="missing_url",
            )
        return Meeting(
            provider_meeting_id=join_url,
            join_url=join_url,
        )

    async def update_meeting(
        self, provider_meeting_id: str, config: MeetingConfig
    ) -> Meeting:
        join_url = config.settings.get("join_url", provider_meeting_id)
        return Meeting(
            provider_meeting_id=join_url,
            join_url=join_url,
        )

    async def delete_meeting(self, provider_meeting_id: str) -> None:
        pass

    async def get_meeting(self, provider_meeting_id: str) -> Optional[Meeting]:
        return Meeting(
            provider_meeting_id=provider_meeting_id,
            join_url=provider_meeting_id,
        )
