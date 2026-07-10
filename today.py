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


def format_int(n: int) -> str:
	"""Thousands-separated integer, e.g. 1234567 -> '1,234,567'."""
	return f"{n:,}"


def _plural(n: int, unit: str) -> str:
	return f"{n} {unit}" + ("" if n == 1 else "s")


def format_uptime(start: datetime.date, today_date: datetime.date) -> str:
	"""Return 'N years, M months, D days' elapsed from start to today_date."""
	if today_date < start:
		raise ValueError("today_date precedes start date")
	years = today_date.year - start.year
	months = today_date.month - start.month
	days = today_date.day - start.day
	if days < 0:
		first_of_this_month = today_date.replace(day=1)
		last_month_end = first_of_this_month - datetime.timedelta(days=1)
		days += last_month_end.day
		months -= 1
	if months < 0:
		months += 12
		years -= 1
	return f"{_plural(years, 'year')}, {_plural(months, 'month')}, {_plural(days, 'day')}"
