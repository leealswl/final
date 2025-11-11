"""
Configuration package for Alice Consultant FastAPI
"""

from .settings import Settings, get_settings

__all__ = [
    "Settings",
    "get_settings",
]
