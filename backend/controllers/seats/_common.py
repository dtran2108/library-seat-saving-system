"""Shared constants, formatting helpers, and query helpers for the seats
package. Anything more than one submodule needs lives here."""
from datetime import datetime, timedelta

from db import query_db, get_db


# ─── Constants ────────────────────────────────────────────────────────────
DATETIME_FORMAT        = '%Y-%m-%d %H:%M:%S'
INPUT_DATETIME_FORMAT  = '%Y-%m-%d %H:%M'
MAX_HOURS_PER_DAY      = 4
ALLOWED_DURATIONS      = (1, 2, 3, 4)
CHECK_IN_GRACE_MINUTES = 30
LIVE_STATUSES          = ('upcoming', 'active')


# ─── Formatting helpers ──────────────────────────────────────────────────
def _parse_booking_datetime(booking_date, start_time):
    return datetime.strptime(f'{booking_date} {start_time}', INPUT_DATETIME_FORMAT)


def _fmt(dt):
    return dt.strftime(DATETIME_FORMAT)


def _now_text():
    return _fmt(datetime.now())


def _reservation_hours(row):
    start_dt = datetime.strptime(row['startTime'], DATETIME_FORMAT)
    end_dt   = datetime.strptime(row['endTime'],   DATETIME_FORMAT)
    return (end_dt - start_dt).total_seconds() / 3600


# ─── Input validation ────────────────────────────────────────────────────
def _validate_window(booking_date, start_time, duration):
    """Parse (booking_date, start_time, duration) into datetimes. Returns
    (start_dt, end_dt, duration_int) or raises ValueError with a user-facing
    message."""
    try:
        duration = int(duration)
    except (TypeError, ValueError):
        raise ValueError('Invalid duration.')
    if duration not in ALLOWED_DURATIONS:
        raise ValueError(f'Duration must be between 1 and {MAX_HOURS_PER_DAY} hours.')

    try:
        start_dt = _parse_booking_datetime(booking_date, start_time)
    except (TypeError, ValueError):
        raise ValueError('Invalid date or time format.')

    return start_dt, start_dt + timedelta(hours=duration), duration


# ─── Overlap / occupancy SQL helpers ─────────────────────────────────────
def _seat_overlap_reservation_id(seat_id, start_text, end_text, exclude_id=None):
    """Return the id of any upcoming/active reservation on this seat that
    overlaps [start_text, end_text), or None if the seat is free."""
    args = [seat_id, end_text, start_text]
    exclude_clause = ''
    if exclude_id is not None:
        exclude_clause = 'AND reservationId != ?'
        args.append(exclude_id)

    row = query_db(
        f"""
        SELECT reservationId
        FROM reservations
        WHERE seatId = ?
        AND status IN ('upcoming', 'active')
        AND startTime < ?
        AND endTime > ?
        {exclude_clause}
        """,
        tuple(args),
        one=True,
    )
    return row['reservationId'] if row else None


def _user_overlap_reservation_id(user_id, start_text, end_text):
    row = query_db(
        """
        SELECT reservationId
        FROM reservations
        WHERE uId = ?
        AND status IN ('upcoming', 'active')
        AND startTime < ?
        AND endTime > ?
        """,
        (user_id, start_text, end_text),
        one=True,
    )
    return row['reservationId'] if row else None


def _seat_active_reservation_at(seat_id, when_text):
    row = query_db(
        """
        SELECT reservationId
        FROM reservations
        WHERE seatId = ?
        AND status = 'active'
        AND startTime <= ?
        AND endTime > ?
        """,
        (seat_id, when_text, when_text),
        one=True,
    )
    return row['reservationId'] if row else None


def _recompute_seat_status(seat_id, when_text=None):
    """Set the seat to 'occupied' iff an active reservation covers `when_text`,
    otherwise 'available'. Leaves blocked seats alone."""
    when_text = when_text or _now_text()
    new_status = 'occupied' if _seat_active_reservation_at(seat_id, when_text) else 'available'
    get_db().execute(
        "UPDATE seats SET status = ? WHERE seatId = ? AND status != 'blocked'",
        (new_status, seat_id),
    )
