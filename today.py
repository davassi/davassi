"""Generate the neofetch-style profile SVGs for github.com/davassi."""
from __future__ import annotations

import datetime
import time
import xml.etree.ElementTree as ET
from typing import Any

import requests

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


SVG_NS: str = "http://www.w3.org/2000/svg"

ET.register_namespace("", SVG_NS)


def find_and_replace(root: ET.Element, element_id: str, value: str) -> None:
	"""Set the text of the <tspan id=element_id> in an SVG tree."""
	el = root.find(f".//{{{SVG_NS}}}tspan[@id='{element_id}']")
	if el is None:
		raise KeyError(f"tspan id '{element_id}' not found in SVG")
	el.text = value


def inject_ascii(root: ET.Element, lines: list[str]) -> None:
	"""Replace children of <text id='ascii'> with one <tspan> per line."""
	ascii_el = root.find(f".//{{{SVG_NS}}}text[@id='ascii']")
	if ascii_el is None:
		raise KeyError("text id 'ascii' not found in SVG")
	x = ascii_el.get("x", "0")
	for child in list(ascii_el):
		ascii_el.remove(child)
	ascii_el.text = None
	for i, line in enumerate(lines):
		tspan = ET.SubElement(ascii_el, f"{{{SVG_NS}}}tspan")
		tspan.set("x", x)
		tspan.set("dy", "0" if i == 0 else "1.15em")
		tspan.text = line


def overwrite_svg(path: str, replacements: dict[str, str], ascii_lines: list[str]) -> None:
	"""Substitute all dynamic values + ASCII art into an SVG file in place."""
	tree = ET.parse(path)
	root = tree.getroot()
	inject_ascii(root, ascii_lines)
	for element_id, value in replacements.items():
		find_and_replace(root, element_id, value)
	tree.write(path, encoding="utf-8", xml_declaration=True)


def graphql(query: str, variables: dict[str, Any], token: str) -> dict[str, Any]:
	"""POST a GraphQL query, retrying transient failures. Returns the data object."""
	headers = {"Authorization": f"Bearer {token}"}
	last_error: Exception | None = None
	for attempt in range(1, MAX_RETRIES + 1):
		try:
			resp = requests.post(
				API_URL,
				json={"query": query, "variables": variables},
				headers=headers,
				timeout=REQUEST_TIMEOUT,
			)
			if resp.status_code >= 500:
				raise requests.HTTPError(f"server error {resp.status_code}")
			resp.raise_for_status()
			payload = resp.json()
			if payload.get("errors"):
				raise RuntimeError(f"GraphQL errors: {payload['errors']}")
			return payload["data"]
		except (requests.RequestException, RuntimeError) as exc:
			last_error = exc
			is_graphql_error = isinstance(exc, RuntimeError) and "GraphQL errors" in str(exc)
			if is_graphql_error or attempt == MAX_RETRIES:
				break
			time.sleep(RETRY_BACKOFF_SECONDS * attempt)
	raise RuntimeError(f"GraphQL request failed: {last_error}")
