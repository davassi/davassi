import datetime

import pytest

import today


def test_format_int_thousands():
    assert today.format_int(0) == "0"
    assert today.format_int(1234567) == "1,234,567"


def test_uptime_exact_years_singular_and_plural():
    start = datetime.date(2011, 1, 1)
    assert today.format_uptime(start, datetime.date(2012, 1, 1)) == "1 year, 0 months, 0 days"
    assert today.format_uptime(start, datetime.date(2013, 2, 1)) == "2 years, 1 month, 0 days"


def test_uptime_borrows_days_and_months():
    start = datetime.date(2011, 3, 15)
    # 2026-03-10 is just short of 15 full years: borrow a month and days.
    assert today.format_uptime(start, datetime.date(2026, 3, 10)) == "14 years, 11 months, 23 days"


def test_uptime_rejects_future_start():
    with pytest.raises(ValueError):
        today.format_uptime(datetime.date(2030, 1, 1), datetime.date(2026, 1, 1))
