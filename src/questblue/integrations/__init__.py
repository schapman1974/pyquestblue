"""Optional web-framework adapters for QuestBlue callbacks."""

from .django import parse_django_request
from .fastapi import parse_fastapi_request

__all__ = ["parse_django_request", "parse_fastapi_request"]
