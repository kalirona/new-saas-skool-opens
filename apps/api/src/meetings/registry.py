from typing import Dict, Type
from src.meetings.base import MeetingProvider


class MeetingProviderRegistry:
    _providers: Dict[str, Type[MeetingProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[MeetingProvider]) -> None:
        cls._providers[name] = provider_cls

    @classmethod
    def get(cls, name: str) -> Type[MeetingProvider]:
        if name not in cls._providers:
            raise KeyError(f"Meeting provider '{name}' not registered")
        return cls._providers[name]

    @classmethod
    def create_instance(cls, name: str, config: dict) -> MeetingProvider:
        provider_cls = cls.get(name)
        return provider_cls(config)

    @classmethod
    def is_supported(cls, name: str) -> bool:
        return name in cls._providers

    @classmethod
    def list_supported(cls) -> list:
        return list(cls._providers.keys())
