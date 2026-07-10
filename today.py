"""Generate the neofetch-style profile SVGs for github.com/davassi."""
from __future__ import annotations

import datetime

USERNAME: str = "davassi"
START_DATE: datetime.date = datetime.date(2011, 1, 1)
OWNER_AFFILIATIONS: list[str] = ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"]

API_URL: str = "https://api.github.com/graphql"
CACHE_PATH: str = "assets/loc_cache.txt"
SVG_FILES: list[str] = ["assets/dark_mode.svg", "assets/light_mode.svg"]

MAX_RETRIES: int = 3
REQUEST_TIMEOUT: int = 30
RETRY_BACKOFF_SECONDS: float = 2.0
