"""Search-and-book user flow: list available seats, check eligibility, and
create the reservation. Also the supporting daily-hours and active-penalty
gates that book_seat enforces."""
from datetime import datetime

from db import query_db, get_db
from controllers.system import is_booking_enabled

from ._common import (
    MAX_HOURS_PER_DAY,
    _fmt,
    _validate_window,
    _reservation_hours,
    _seat_overlap_reservation_id,
    _user_overlap_reservation_id,
)


def get_available_seats(booking_date, start_time, duration, zone_id=None):
    """Return seats available for the requested time range."""
    if not all([booking_date, start_time, duration]):
        return False, 'booking_date, start_time, and duration are required.'

    try:
        start_dt, end_dt, _ = _validate_window(booking_date, start_time, duration)
    except ValueError as e:
        return False, str(e)

    params = [_fmt(end_dt), _fmt(start_dt)]
    zone_filter = ''
    if zone_id:
        try:
            zone_id = int(zone_id)
        except (TypeError, ValueError):
            return False, 'Invalid zone ID.'
        zone_filter = 'AND s.zoneId = ?'
        params.append(zone_id)

    seats = query_db(
        f"""
        SELECT s.seatId, s.deskNo, s.status, s.zoneId, z.name AS zoneName
        FROM seats s
        JOIN zones z ON s.zoneId = z.zoneId
        WHERE s.status != 'blocked'
        AND z.status != 'maintenance'
        AND NOT EXISTS (
            SELECT 1 FROM reservations r
            WHERE r.seatId = s.seatId
            AND r.status IN ('upcoming', 'active')
            AND r.startTime < ?
            AND r.endTime > ?
        )
        {zone_filter}
        ORDER BY z.zoneId, s.deskNo
        """,
        tuple(params),
    )
    return True, [dict(s) for s in seats]


def _get_user_daily_hours(user_id, booking_date):
    reservations = query_db(
        """
        SELECT startTime, endTime
        FROM reservations
        WHERE uId = ?
        AND status IN ('upcoming', 'active')
        AND startTime BETWEEN ? AND ?
        """,
        (user_id, f'{booking_date} 00:00:00', f'{booking_date} 23:59:59'),
    )
    return sum(_reservation_hours(r) for r in reservations)


def _active_penalty_for_user(user_id):
    """Return the user's current active penalty row, or None. Expires any
    stale penalties first so a row past its endDate never blocks a booking."""
    today = datetime.now().strftime('%Y-%m-%d')
    db = get_db()
    db.execute(
        "UPDATE penalties SET status = 'expired' WHERE status = 'active' AND endDate < ?",
        (today,),
    )
    db.commit()

    return query_db(
        """
        SELECT p.penaltyId, p.reason, p.endDate
        FROM penalties p
        JOIN reservations r ON r.reservationId = p.reservationId
        WHERE r.uId = ?
        AND p.status = 'active'
        LIMIT 1
        """,
        (user_id,),
        one=True,
    )


def book_seat(user_id, seat_id, booking_date, start_time, duration):
    """Reserve a seat. Returns (True, msg) or (False, err)."""
    if not is_booking_enabled():
        return False, 'Bookings are temporarily disabled by the library staff.'

    if not all([seat_id, booking_date, start_time, duration]):
        return False, 'All fields are required.'

    try:
        seat_id = int(seat_id)
    except (TypeError, ValueError):
        return False, 'Invalid seat ID.'

    try:
        start_dt, end_dt, duration = _validate_window(booking_date, start_time, duration)
    except ValueError as e:
        return False, str(e)

    if _get_user_daily_hours(user_id, booking_date) + duration > MAX_HOURS_PER_DAY:
        return False, f'You can book at most {MAX_HOURS_PER_DAY} hours per day.'

    penalty = _active_penalty_for_user(user_id)
    if penalty:
        return False, (
            f'Booking blocked: you have an active penalty until '
            f'{penalty["endDate"]} ({penalty["reason"]}).'
        )

    seat = query_db(
        """
        SELECT s.seatId, s.status, z.status AS zone_status
        FROM seats s
        JOIN zones z ON s.zoneId = z.zoneId
        WHERE s.seatId = ?
        """,
        (seat_id,),
        one=True,
    )
    if not seat:
        return False, 'Seat not found.'
    if seat['status'] == 'blocked' or seat['zone_status'] == 'maintenance':
        return False, 'This seat is not available.'

    start_text, end_text = _fmt(start_dt), _fmt(end_dt)

    if _seat_overlap_reservation_id(seat_id, start_text, end_text):
        return False, 'This seat is already booked during that time.'
    if _user_overlap_reservation_id(user_id, start_text, end_text):
        return False, 'You already have a booking during that time.'

    now = datetime.now()
    is_active_now = start_dt <= now < end_dt
    status = 'active' if is_active_now else 'upcoming'

    db = get_db()
    db.execute(
        """
        INSERT INTO reservations (uId, seatId, startTime, endTime, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, seat_id, start_text, end_text, status),
    )
    if is_active_now:
        db.execute(
            "UPDATE seats SET status = 'occupied' WHERE seatId = ? AND status != 'blocked'",
            (seat_id,),
        )

    db.commit()
    return True, 'Seat booked successfully!'
