import textwrap
import xml.etree.ElementTree as ET

import pytest

import today

MINI_SVG = textwrap.dedent(
    """\
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <text id="ascii" x="5" y="10"></text>
      <text x="60" y="10"><tspan id="repo_data">...</tspan></text>
    </svg>
    """
)


def _write(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return str(p)


def test_find_and_replace_sets_text():
    root = ET.fromstring(MINI_SVG)
    today.find_and_replace(root, "repo_data", "42")
    el = root.find(f".//{{{today.SVG_NS}}}tspan[@id='repo_data']")
    assert el.text == "42"


def test_find_and_replace_missing_id_raises():
    root = ET.fromstring(MINI_SVG)
    with pytest.raises(KeyError):
        today.find_and_replace(root, "nope", "x")


def test_inject_ascii_creates_one_tspan_per_line():
    root = ET.fromstring(MINI_SVG)
    today.inject_ascii(root, ["line-a", "line-b", "line-c"])
    ascii_el = root.find(f".//{{{today.SVG_NS}}}text[@id='ascii']")
    tspans = ascii_el.findall(f"{{{today.SVG_NS}}}tspan")
    assert [t.text for t in tspans] == ["line-a", "line-b", "line-c"]


def test_overwrite_svg_roundtrip(tmp_path):
    path = _write(tmp_path, "m.svg", MINI_SVG)
    today.overwrite_svg(path, {"repo_data": "99"}, ["AA", "BB"])
    out = (tmp_path / "m.svg").read_text(encoding="utf-8")
    assert "99" in out
    assert "AA" in out and "BB" in out
    # Namespace stays clean (no ns0: prefixes that break rendering).
    assert "ns0:" not in out
