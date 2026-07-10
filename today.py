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


def fetch_account(token: str) -> tuple[str, str]:
	"""Return (node_id, created_at_iso) for USERNAME."""
	query = "query($login:String!){ user(login:$login){ id createdAt } }"
	user = graphql(query, {"login": USERNAME}, token)["user"]
	return user["id"], user["createdAt"]


def fetch_repositories(token: str) -> list[dict[str, Any]]:
	"""Owner repos (private included, forks excluded), paginated."""
	query = """
	query($login:String!,$affs:[RepositoryAffiliation],$cursor:String){
	  user(login:$login){
	    repositories(first:100, after:$cursor, ownerAffiliations:$affs,
	                 orderBy:{field:STARGAZERS, direction:DESC}){
	      pageInfo{ hasNextPage endCursor }
	      nodes{
	        nameWithOwner isFork stargazerCount
	        defaultBranchRef{ target{ ... on Commit{ oid history{ totalCount } } } }
	      }
	    }
	  }
	}"""
	repos: list[dict[str, Any]] = []
	cursor: str | None = None
	while True:
		data = graphql(query, {"login": USERNAME, "affs": OWNER_AFFILIATIONS, "cursor": cursor}, token)
		conn = data["user"]["repositories"]
		for node in conn["nodes"]:
			if node["isFork"]:
				continue
			branch = node.get("defaultBranchRef")
			target = branch["target"] if branch else None
			repos.append({
				"name_with_owner": node["nameWithOwner"],
				"stars": node["stargazerCount"],
				"default_branch_oid": target["oid"] if target else None,
				"history_count": target["history"]["totalCount"] if target else 0,
			})
		if not conn["pageInfo"]["hasNextPage"]:
			return repos
		cursor = conn["pageInfo"]["endCursor"]


def fetch_star_total(repos: list[dict[str, Any]]) -> int:
	return sum(r["stars"] for r in repos)


def fetch_contributed_count(token: str) -> int:
	query = """query($login:String!){
	  user(login:$login){
	    repositoriesContributedTo(includeUserRepositories:false,
	      contributionTypes:[COMMIT,PULL_REQUEST,REPOSITORY]){ totalCount }
	  }}"""
	return graphql(query, {"login": USERNAME}, token)["user"]["repositoriesContributedTo"]["totalCount"]


def fetch_follower_count(token: str) -> int:
	query = "query($login:String!){ user(login:$login){ followers{ totalCount } } }"
	return graphql(query, {"login": USERNAME}, token)["user"]["followers"]["totalCount"]


def parse_cache(text: str) -> dict[str, dict[str, int | str]]:
	cache: dict[str, dict[str, int | str]] = {}
	for line in text.splitlines():
		if not line.strip():
			continue
		name, oid, hist, add, dele, commits = line.split("\t")
		cache[name] = {"oid": oid, "history_count": int(hist),
					   "add": int(add), "del": int(dele), "commits": int(commits)}
	return cache


def serialize_cache(cache: dict[str, dict[str, int | str]]) -> str:
	lines = []
	for name, e in cache.items():
		lines.append("\t".join(str(x) for x in
						 [name, e["oid"], e["history_count"], e["add"], e["del"], e["commits"]]))
	return "\n".join(lines) + ("\n" if lines else "")


def count_repo_history(name_with_owner: str, author_id: str, token: str) -> tuple[int, int, int]:
	"""Sum additions/deletions and count commits authored by author_id in a repo."""
	owner, name = name_with_owner.split("/", 1)
	query = """
	query($owner:String!,$name:String!,$author:ID!,$cursor:String){
	  repository(owner:$owner,name:$name){
	    defaultBranchRef{ target{ ... on Commit{
	      history(first:100, after:$cursor, author:{id:$author}){
	        pageInfo{ hasNextPage endCursor }
	        edges{ node{ additions deletions } }
	      }}}}
	  }}"""
	add = dele = commits = 0
	cursor: str | None = None
	while True:
		data = graphql(query, {"owner": owner, "name": name, "author": author_id, "cursor": cursor}, token)
		branch = data["repository"]["defaultBranchRef"]
		if not branch:
			return add, dele, commits
		history = branch["target"]["history"]
		for edge in history["edges"]:
			add += edge["node"]["additions"]
			dele += edge["node"]["deletions"]
			commits += 1
		if not history["pageInfo"]["hasNextPage"]:
			return add, dele, commits
		cursor = history["pageInfo"]["endCursor"]


def count_lines(repos: list[dict[str, Any]], author_id: str, token: str,
				cache: dict[str, dict[str, int | str]]) -> tuple[int, int, int, int, dict]:
	"""Aggregate LOC add/del/total and commits across repos, reusing the cache."""
	total_add = total_del = total_commits = 0
	new_cache: dict[str, dict[str, int | str]] = {}
	for repo in repos:
		name = repo["name_with_owner"]
		oid = repo["default_branch_oid"]
		hist = repo["history_count"]
		cached = cache.get(name)
		if cached and cached["oid"] == oid and cached["history_count"] == hist:
			add, dele, commits = int(cached["add"]), int(cached["del"]), int(cached["commits"])
		elif oid is None:
			add = dele = commits = 0
		else:
			add, dele, commits = count_repo_history(name, author_id, token)
		new_cache[name] = {"oid": oid, "history_count": hist, "add": add, "del": dele, "commits": commits}
		total_add += add
		total_del += dele
		total_commits += commits
	return total_add, total_del, total_add - total_del, total_commits, new_cache
