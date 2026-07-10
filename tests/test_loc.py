from typing import Any

import today


def test_cache_roundtrip():
    cache = {"davassi/a": {"oid": "aaa", "history_count": 30, "add": 100, "del": 20, "commits": 25}}
    text = today.serialize_cache(cache)
    assert today.parse_cache(text) == cache


def test_count_lines_uses_cache_for_unchanged_repo(monkeypatch):
    # Repo 'a' unchanged (same oid + history_count) -> served from cache, no API call.
    repos = [{"name_with_owner": "davassi/a", "stars": 1,
              "default_branch_oid": "aaa", "history_count": 30}]
    cache = {"davassi/a": {"oid": "aaa", "history_count": 30, "add": 100, "del": 20, "commits": 25}}

    def boom(*args, **kwargs):
        raise AssertionError("should not hit API for cached repo")

    monkeypatch.setattr(today, "count_repo_history", boom)
    add, dele, total, commits, new_cache = today.count_lines(repos, "U_1", "tok", cache)
    assert (add, dele, total, commits) == (100, 20, 80, 25)
    assert new_cache["davassi/a"]["add"] == 100


def test_count_lines_recomputes_changed_repo(monkeypatch):
    repos = [{"name_with_owner": "davassi/a", "stars": 1,
              "default_branch_oid": "NEWoid", "history_count": 31}]
    cache = {"davassi/a": {"oid": "aaa", "history_count": 30, "add": 100, "del": 20, "commits": 25}}
    monkeypatch.setattr(today, "count_repo_history", lambda n, a, t: (150, 30, 31))
    add, dele, total, commits, new_cache = today.count_lines(repos, "U_1", "tok", cache)
    assert (add, dele, total, commits) == (150, 30, 120, 31)
    assert new_cache["davassi/a"]["oid"] == "NEWoid"


def test_count_repo_history_paginates(monkeypatch):
    page1 = {"repository": {"defaultBranchRef": {"target": {"history": {
        "pageInfo": {"hasNextPage": True, "endCursor": "c1"},
        "edges": [{"node": {"additions": 10, "deletions": 2}},
                  {"node": {"additions": 5, "deletions": 1}}]}}}}}
    page2 = {"repository": {"defaultBranchRef": {"target": {"history": {
        "pageInfo": {"hasNextPage": False, "endCursor": None},
        "edges": [{"node": {"additions": 7, "deletions": 3}}]}}}}}
    seq = iter([page1, page2])
    monkeypatch.setattr(today, "graphql", lambda q, v, t: next(seq))
    add, dele, commits = today.count_repo_history("davassi/a", "U_1", "tok")
    assert (add, dele, commits) == (22, 6, 3)
