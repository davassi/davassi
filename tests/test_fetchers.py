from typing import Any

import today


def make_graphql(responses: list[dict[str, Any]]):
    seq = iter(responses)

    def _graphql(query: str, variables: dict[str, Any], token: str) -> dict[str, Any]:
        return next(seq)

    return _graphql


def test_fetch_account(monkeypatch):
    monkeypatch.setattr(
        today, "graphql",
        make_graphql([{"user": {"id": "U_1", "createdAt": "2012-03-23T12:32:03Z"}}]),
    )
    assert today.fetch_account("tok") == ("U_1", "2012-03-23T12:32:03Z")


def test_fetch_repositories_paginates_and_skips_forks(monkeypatch):
    page1 = {"user": {"repositories": {
        "pageInfo": {"hasNextPage": True, "endCursor": "c1"},
        "nodes": [
            {"nameWithOwner": "davassi/a", "isFork": False, "stargazerCount": 17,
             "defaultBranchRef": {"target": {"oid": "aaa", "history": {"totalCount": 30}}}},
            {"nameWithOwner": "davassi/fork", "isFork": True, "stargazerCount": 0,
             "defaultBranchRef": None},
        ]}}}
    page2 = {"user": {"repositories": {
        "pageInfo": {"hasNextPage": False, "endCursor": None},
        "nodes": [
            {"nameWithOwner": "davassi/b", "isFork": False, "stargazerCount": 5,
             "defaultBranchRef": {"target": {"oid": "bbb", "history": {"totalCount": 12}}}},
        ]}}}
    monkeypatch.setattr(today, "graphql", make_graphql([page1, page2]))
    repos = today.fetch_repositories("tok")
    names = [r["name_with_owner"] for r in repos]
    assert names == ["davassi/a", "davassi/b"]
    assert repos[0] == {"name_with_owner": "davassi/a", "stars": 17,
                        "default_branch_oid": "aaa", "history_count": 30}
    assert today.fetch_star_total(repos) == 22


def test_fetch_contributed_and_followers(monkeypatch):
    monkeypatch.setattr(
        today, "graphql",
        make_graphql([{"user": {"repositoriesContributedTo": {"totalCount": 133}}}]),
    )
    assert today.fetch_contributed_count("tok") == 133
    monkeypatch.setattr(
        today, "graphql",
        make_graphql([{"user": {"followers": {"totalCount": 39}}}]),
    )
    assert today.fetch_follower_count("tok") == 39
