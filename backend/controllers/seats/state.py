"""Reservation/seat state transitions:
   - timed sweeps that roll reservations forward and recompute seat occupancy,
   - the missed-check-in sweep that releases seats whose user never showed up,
   - the user-initiated check-in flow."""
from datetime import datetime, timedelta

from db import query_db, get_db

from ._common import (
    DATETIME_FORMAT,
    CHECK_IN_GRACE_MINUTES,
    _fmt,
    _now_text,
)


def update_expired_reservations():
    """Roll reservation statuses forward in time, then recompute seat
    occupancy from the active reservation set."""
    now_text = _now_text()
    db = get_db()

    db.execute(
        """
        UPDATE reservations
        SET status = 'completed'
        WHERE status IN ('active', 'upcoming')
        AND endTime <= ?
        """,
        (now_text,),
    )

    db.execute(
        """
        UPDATE reservations
        SET status = 'active'
        WHERE status = 'upcoming'
        AND startTime <= ?
        AND endTime > ?
        """,
        (now_text, now_text),
    )

    db.execute(
        """
        UPDATE seats
        SET status = CASE
            WHEN EXISTS (
                SELECT 1 FROM reservations
                WHERE seatId = seats.seatId
                AND status = 'active'
                AND startTime <= ?
                AND endTime > ?
            ) THEN 'occupied'
            ELSE 'available'
        END
        WHERE status != 'blocked'
        """,
        (now_text, now_text),
    )

    db.commit()

    sweep_missed_check_ins()


def sweep_missed_check_ins():
    """Release seats whose user did not check in within the grace period.

    Insert a placeholder check-in log row and update it to 'missed' so the
    auto_release_seat trigger (schema.sql) cascades to no_show + seat release.
    """
    now = datetime.now()
    cutoff_text = _fmt(now - timedelta(minutes=CHECK_IN_GRACE_MINUTES))
    now_text = _fmt(now)

    missed = query_db(
        """
        SELECT r.reservationId
        FROM reservations r
        LEFT JOIN check_in_logs c ON c.reservationId = r.reservationId
        WHERE r.status IN ('upcoming', 'active')
        AND r.startTime <= ?
        AND r.endTime > ?
        AND c.checkInId IS NULL
        """,
        (cutoff_text, now_text),
    )

    if not missed:
        return

    db = get_db()
    for row in missed:
        db.execute(
            "INSERT INTO check_in_logs (reservationId, status) VALUES (?, 'checked_in')",
            (row['reservationId'],),
        )
        db.execute(
            "UPDATE check_in_logs SET status = 'missed' WHERE reservationId = ?",
            (row['reservationId'],),
        )
    db.commit()


def check_in_reservation(reservation_id, user_id):
    """User checks in for their reservation. Returns (success, msg)."""
    try:
        reservation_id = int(reservation_id)
    except (TypeError, ValueError):
        return False, 'Invalid reservation ID.'

    row = query_db(
        """
        SELECT r.uId, r.startTime, r.status, c.checkInId
        FROM reservations r
        LEFT JOIN check_in_logs c ON c.reservationId = r.reservationId
        WHERE r.reservationId = ?
        """,
        (reservation_id,),
        one=True,
    )

    if not row:
        return False, 'Reservation not found.'
    if row['uId'] != user_id:
        return False, 'You can only check in to your own reservation.'
    if row['checkInId'] is not None:
        return False, 'You have already checked in for this reservation.'
    if row['status'] != 'active':
        return False, 'Check-in is only available for active reservations.'

    now = datetime.now()
    start_dt = datetime.strptime(row['startTime'], DATETIME_FORMAT)
    if now > start_dt + timedelta(minutes=CHECK_IN_GRACE_MINUTES):
        return False, 'The 30-minute check-in window has expired.'

    get_db().execute(
        """
        INSERT INTO check_in_logs (reservationId, checkInTime, status)
        VALUES (?, ?, 'checked_in')
        """,
        (reservation_id, _fmt(now)),
    )
    get_db().commit()
    return True, 'Checked in successfully.'
