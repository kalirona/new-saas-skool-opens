"""Centralized branding configuration for the backend.

Single source of truth for app name, description, and related branding values.
Callers should import from here instead of hardcoding "LearnHouse".
"""

from config.config import get_learnhouse_config


def get_app_name() -> str:
    """Return the configured site name (default: 'LearnHouse')."""
    cfg = get_learnhouse_config()
    return getattr(cfg, "site_name", None) or "LearnHouse"


def get_app_description() -> str:
    """Return the configured site description."""
    cfg = get_learnhouse_config()
    return getattr(cfg, "site_description", None) or "LearnHouse - Open source learning platform"


def get_sender_name() -> str:
    """Return the email sender display name."""
    return get_app_name()


def get_support_url() -> str:
    """Return the support page URL."""
    import os
    platform = os.environ.get("LEARNHOUSE_PLATFORM_URL", "https://www.learnhouse.app").rstrip("/")
    return f"{platform}/dashboard/support"
