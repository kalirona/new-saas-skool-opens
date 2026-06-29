from typing import Dict, Optional, Type
from src.billing.base import BillingProvider


class BillingProviderRegistry:
    """
    Registry for billing provider implementations.

    Providers register themselves here at startup. The core code
    looks up providers by name and never imports provider-specific
    modules directly.
    """

    _providers: Dict[str, Type[BillingProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[BillingProvider]) -> None:
        """
        Register a billing provider class.

        Called during provider module import (which happens at
        application startup).
        """
        cls._providers[name.lower()] = provider_cls

    @classmethod
    def get(cls, name: str) -> Optional[Type[BillingProvider]]:
        """Get a provider class by name. Returns None if not registered."""
        return cls._providers.get(name.lower())

    @classmethod
    def get_all(cls) -> Dict[str, Type[BillingProvider]]:
        """Return all registered providers."""
        return dict(cls._providers)

    @classmethod
    def is_supported(cls, name: str) -> bool:
        """Check if a provider name is registered."""
        return name.lower() in cls._providers

    @classmethod
    def list_supported(cls) -> list[str]:
        """Return list of supported provider names."""
        return list(cls._providers.keys())

    @classmethod
    def create_instance(cls, name: str, config: Optional[dict] = None) -> Optional[BillingProvider]:
        """
        Create an instance of a registered provider.

        Args:
            name: Provider name (case-insensitive)
            config: Optional configuration dict passed to the constructor

        Returns:
            BillingProvider instance or None if not registered
        """
        provider_cls = cls.get(name)
        if not provider_cls:
            return None
        return provider_cls(config or {})
