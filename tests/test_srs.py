from datetime import UTC, datetime

import pytest

from backend.srs import schedule_review


@pytest.mark.parametrize("rating,interval,repetitions", [(1, 0, 0), (2, 1, 0), (3, 1, 1), (4, 6, 1)])
def test_first_review_uses_expected_interval(rating, interval, repetitions):
    result = schedule_review(2.5, 0, 0, rating, now=datetime(2026, 1, 1, tzinfo=UTC))
    assert result["interval_days"] == interval
    assert result["repetitions"] == repetitions


def test_good_review_advances_sm2_sequence():
    result = schedule_review(2.5, 1, 1, 3, now=datetime(2026, 1, 1, tzinfo=UTC))
    assert result["interval_days"] == 6
    assert result["repetitions"] == 2
    assert result["next_review_at"].startswith("2026-01-07")
