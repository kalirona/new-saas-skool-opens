"""
Meeting provider abstraction — modelled after BillingProvider.

Providers implement create/update/delete meeting links and
optionally generate join URLs, host keys, and webhook handling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


class MeetingProviderError(Exception):
    def __init__(self, message: str, provider: str, code: Optional[str] = None):
        self.provider = provider
        self.code = code
        super().__init__(message)


@dataclass
class MeetingConfig:
    """Configuration required to create a meeting."""
    title: str
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    timezone: Optional[str] = None
    duration_minutes: Optional[int] = None
    max_participants: Optional[int] = None
    host_email: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Meeting:
    """A meeting resource created on the provider."""
    provider_meeting_id: str
    join_url: str
    host_url: Optional[str] = None
    host_key: Optional[str] = None
    dial_in: Optional[str] = None
    start_url: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)


class MeetingProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def create_meeting(self, config: MeetingConfig) -> Meeting:
        pass

    @abstractmethod
    async def update_meeting(
        self, provider_meeting_id: str, config: MeetingConfig
    ) -> Meeting:
        pass

    @abstractmethod
    async def delete_meeting(self, provider_meeting_id: str) -> None:
        pass

    @abstractmethod
    async def get_meeting(self, provider_meeting_id: str) -> Optional[Meeting]:
        pass

    async def handle_webhook(
        self, raw_body: bytes, signature_header: Optional[str] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError(f"{self.provider_name} does not support webhooks")
