import datetime

import today


def test_config_constants_present_and_typed():
    assert today.USERNAME == "davassi"
    assert today.START_DATE == datetime.date(2011, 1, 1)
    assert "OWNER" in today.OWNER_AFFILIATIONS
    assert today.API_URL == "https://api.github.com/graphql"
    assert today.SVG_FILES == ["assets/dark_mode.svg", "assets/light_mode.svg"]
    assert today.CACHE_PATH == "assets/loc_cache.txt"
    assert today.MAX_RETRIES >= 1
    assert today.REQUEST_TIMEOUT > 0
