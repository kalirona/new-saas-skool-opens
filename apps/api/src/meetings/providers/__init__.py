from src.meetings.providers.zoom import ZoomMeetingProvider
from src.meetings.providers.google_meet import GoogleMeetMeetingProvider
from src.meetings.providers.teams import TeamsMeetingProvider
from src.meetings.providers.custom_url import CustomUrlMeetingProvider
from src.meetings.registry import MeetingProviderRegistry


MeetingProviderRegistry.register("zoom", ZoomMeetingProvider)
MeetingProviderRegistry.register("google_meet", GoogleMeetMeetingProvider)
MeetingProviderRegistry.register("teams", TeamsMeetingProvider)
MeetingProviderRegistry.register("custom_url", CustomUrlMeetingProvider)


__all__ = [
    "ZoomMeetingProvider",
    "GoogleMeetMeetingProvider",
    "TeamsMeetingProvider",
    "CustomUrlMeetingProvider",
]
