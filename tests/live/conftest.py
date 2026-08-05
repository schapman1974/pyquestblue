"""Safety gates shared by tests that contact a real QuestBlue account."""

from __future__ import annotations

import os
from typing import Iterator
from urllib.parse import urlsplit

import pytest

from questblue import QuestBlue

READ_ONLY_ACK = "YES_I_ACCEPT_PRODUCTION_READS"
ALLOWED_HOSTS = frozenset(("api.questblue.com", "api2.questblue.com"))


@pytest.fixture
def live_read_only_client() -> Iterator[QuestBlue]:
    if os.getenv("QUESTBLUE_RUN_LIVE_READ_ONLY") != READ_ONLY_ACK:
        pytest.skip("live reads require explicit production-read acknowledgment")
    required = (
        "QUESTBLUE_LIVE_USERNAME",
        "QUESTBLUE_LIVE_PASSWORD",
        "QUESTBLUE_LIVE_SECURITY_KEY",
        "QUESTBLUE_LIVE_BASE_URL",
    )
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        pytest.skip("missing dedicated live-subaccount settings: " + ", ".join(missing))
    base_url = os.environ["QUESTBLUE_LIVE_BASE_URL"]
    parsed = urlsplit(base_url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        pytest.fail("live base URL must be an HTTPS QuestBlue API host")
    with QuestBlue(
        os.environ["QUESTBLUE_LIVE_USERNAME"],
        os.environ["QUESTBLUE_LIVE_PASSWORD"],
        os.environ["QUESTBLUE_LIVE_SECURITY_KEY"],
        base_url=base_url,
        max_retries=0,
    ) as client:
        yield client
