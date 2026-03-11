"""Utilities for planned-payment template recurrence."""

from datetime import date, timedelta

from app.models.types import Recurrence


def compute_next_due_date(
    start_date: date,
    current_due: date,
    recurrence: Recurrence,
) -> date:
    """Compute the next due date based on a recurrence rule."""
    match recurrence:
        case Recurrence.DAILY:
            return current_due + timedelta(days=1)
        case Recurrence.WEEKLY:
            return current_due + timedelta(weeks=1)
        case Recurrence.MONTHLY:
            year = current_due.year
            month = current_due.month + 1
            if month > 12:
                month = 1
                year += 1

            if month == 12:
                next_month_last_day = 31
            else:
                next_next_month_first = date(year, month + 1, 1)
                next_month_last_day = (next_next_month_first - timedelta(days=1)).day

            day = min(start_date.day, next_month_last_day)
            return date(year, month, day)
        case _:
            raise ValueError(f"Unknown recurrence: {recurrence}")
