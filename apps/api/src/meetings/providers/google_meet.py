"""
Google Meet provider — requires Google Cloud service account with Calendar API.

Credentials: service_account_json (JSON string), delegated_admin email.
"""

import json
from typing import Optional, Dict, Any
from src.meetings.base import (
    MeetingProvider,
    MeetingProviderError,
    MeetingConfig,
    Meeting,
)


class GoogleMeetMeetingProvider(MeetingProvider):
    @property
    def provider_name(self) -> str:
        return "google_meet"

    def __init__(self, config: dict):
        self.service_account_json = config.get("service_account_json", "")
        self.delegated_admin = config.get("delegated_admin", "")
        if not self.service_account_json:
            raise MeetingProviderError(
                "Google Meet requires a service_account_json. "
                "Set LEARNHOUSE_GOOGLE_SERVICE_ACCOUNT_JSON in environment.",
                provider="google_meet",
                code="missing_credentials",
            )

    async def _get_calendar_service(self):
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_info = json.loads(self.service_account_json)
        scopes = ["https://www.googleapis.com/auth/calendar"]
        credentials = service_account.Credentials.from_service_account_info(
            creds_info, scopes=scopes
        )
        if self.delegated_admin:
            credentials = credentials.with_subject(self.delegated_admin)
        return build("calendar", "v3", credentials=credentials)

    async def create_meeting(self, config: MeetingConfig) -> Meeting:
        service = await self._get_calendar_service()
        event_body = {
            "summary": config.title,
            "description": config.description or "",
            "start": {
                "dateTime": config.start_time,
                "timeZone": config.timezone or "UTC",
            },
            "end": {
                "dateTime": config.end_time,
                "timeZone": config.timezone or "UTC",
            },
            "conferenceData": {
                "createRequest": {
                    "requestId": config.metadata.get("request_id", "meet-request"),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
        }
        if config.duration_minutes and config.start_time and not config.end_time:
            from datetime import datetime, timedelta
            try:
                start = datetime.fromisoformat(config.start_time)
                event_body["end"] = {
                    "dateTime": (start + timedelta(minutes=config.duration_minutes)).isoformat(),
                    "timeZone": config.timezone or "UTC",
                }
            except (ValueError, TypeError):
                pass

        event = service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1,
        ).execute()

        conference_data = event.get("conferenceData", {})
        entry_points = conference_data.get("entryPoints", [])
        join_url = ""
        for ep in entry_points:
            if ep.get("entryPointType") == "video":
                join_url = ep.get("uri", "")
                break

        return Meeting(
            provider_meeting_id=event.get("id", ""),
            join_url=join_url,
        )

    async def update_meeting(
        self, provider_meeting_id: str, config: MeetingConfig
    ) -> Meeting:
        service = await self._get_calendar_service()
        event_body = {
            "summary": config.title,
            "description": config.description or "",
        }
        if config.start_time:
            event_body["start"] = {
                "dateTime": config.start_time,
                "timeZone": config.timezone or "UTC",
            }
        if config.end_time:
            event_body["end"] = {
                "dateTime": config.end_time,
                "timeZone": config.timezone or "UTC",
            } or (config.duration_minutes and config.start_time):
            from datetime import datetime, timedelta
            try:
                start = datetime.fromisoformat(config.start_time)
                event_body["end"] = {
                    "dateTime": (start + timedelta(minutes=config.duration_minutes)).isoformat(),
                    "timeZone": config.timezone or "UTC",
                }
            except (ValueError, TypeError):
                pass

        service.events().patch(
            calendarId="primary",
            eventId=provider_meeting_id,
            body=event_body,
        ).execute()

        return Meeting(
            provider_meeting_id=provider_meeting_id,
            join_url="",
        )

    async def delete_meeting(self, provider_meeting_id: str) -> None:
        service = await self._get_calendar_service()
        try:
            service.events().delete(
                calendarId="primary",
                eventId=provider_meeting_id,
            ).execute()
        except Exception as e:
            raise MeetingProviderError(
                f"Failed to delete Google Meet event: {e}",
                provider="google_meet",
                code="delete_failed",
            )

    async def get_meeting(self, provider_meeting_id: str) -> Optional[Meeting]:
        service = await self._get_calendar_service()
        try:
            event = service.events().get(
                calendarId="primary",
                eventId=provider_meeting_id,
            ).execute()
            conference_data = event.get("conferenceData", {})
            entry_points = conference_data.get("entryPoints", [])
            join_url = ""
            for ep in entry_points:
                if ep.get("entryPointType") == "video":
                    join_url = ep.get("uri", "")
                    break
            return Meeting(
                provider_meeting_id=event.get("id", ""),
                join_url=join_url,
            )
        except Exception:
            return None
