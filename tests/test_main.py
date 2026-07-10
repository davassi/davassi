import datetime
import textwrap
import xml.etree.ElementTree as ET

import today

MINI_SVG = textwrap.dedent(
    """\
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <text id="ascii" x="5" y="10"></text>
      <text x="60" y="10">
        <tspan id="uptime">.</tspan><tspan id="repo_data">.</tspan>
        <tspan id="contrib_data">.</tspan><tspan id="star_data">.</tspan>
        <tspan id="commit_data">.</tspan><tspan id="follower_data">.</tspan>
        <tspan id="loc_total">.</tspan><tspan id="loc_add">.</tspan><tspan id="loc_del">.</tspan>
      </text>
    </svg>
    """
)


def test_load_portrait_reads_lines(tmp_path):
    p = tmp_path / "portrait.txt"
    p.write_text("AAA\nBBB\n", encoding="utf-8")
    assert today.load_portrait(str(p)) == ["AAA", "BBB"]


def test_main_writes_all_tokens(tmp_path, monkeypatch):
    svg = tmp_path / "dark_mode.svg"
    svg.write_text(MINI_SVG, encoding="utf-8")
    portrait = tmp_path / "portrait.txt"
    portrait.write_text("X\nY\n", encoding="utf-8")
    cache = tmp_path / "loc_cache.txt"

    monkeypatch.setattr(today, "SVG_FILES", [str(svg)])
    monkeypatch.setattr(today, "CACHE_PATH", str(cache))
    monkeypatch.setattr(today, "fetch_account", lambda t: ("U_1", "2012-03-23T12:32:03Z"))
    monkeypatch.setattr(today, "fetch_repositories", lambda t: [
        {"name_with_owner": "davassi/a", "stars": 17, "default_branch_oid": "aaa", "history_count": 30}])
    monkeypatch.setattr(today, "fetch_contributed_count", lambda t: 133)
    monkeypatch.setattr(today, "fetch_follower_count", lambda t: 39)
    monkeypatch.setattr(today, "count_repo_history", lambda n, a, t: (523178, 76902, 2116))

    result = today.main("tok", datetime.date(2026, 7, 10), str(portrait))

    assert result["repo_data"] == "1"
    assert result["star_data"] == "17"
    assert result["contrib_data"] == "133"
    assert result["follower_data"] == "39"
    assert result["commit_data"] == "2,116"
    assert result["loc_add"] == "523,178"
    assert result["loc_del"] == "76,902"
    assert result["loc_total"] == "446,276"
    assert result["uptime"].endswith("days") and result["uptime"].startswith("15 years")

    root = ET.parse(str(svg)).getroot()
    star_el = root.find(f".//{{{today.SVG_NS}}}tspan[@id='star_data']")
    assert star_el.text == "17"
    assert cache.read_text(encoding="utf-8").startswith("davassi/a\t")
