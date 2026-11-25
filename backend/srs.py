"""SM-2 review scheduling."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


def schedule_review(ease_factor: float, interval_days: int, repetitions: int, rating: int, now: datetime | None = None) -> dict:
    if rating not in {1, 2, 3, 4}:
        raise ValueError("Rating must be between 1 and 4")
    now = now or datetime.now(timezone.utc)
    quality = {1: 0, 2: 2, 3: 4, 4: 5}[rating]
    new_ease = max(1.3, ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    if rating == 1:
        new_interval, new_repetitions = 0, 0
        due = now + timedelta(hours=12)
    elif rating == 2:
        new_interval, new_repetitions = 1, 0
        due = now + timedelta(days=1)
    else:
        new_repetitions = repetitions + 1
        if rating == 4 and repetitions == 0:
            new_interval = 6
        elif new_repetitions == 1:
            new_interval = 1
        elif new_repetitions == 2:
            new_interval = 6
        else:
            multiplier = new_ease * (1.3 if rating == 4 else 1.0)
            new_interval = max(1, round(interval_days * multiplier))
        due = now + timedelta(days=new_interval)
    return {"ease_factor": round(new_ease, 4), "interval_days": new_interval, "repetitions": new_repetitions, "next_review_at": due.isoformat()}
