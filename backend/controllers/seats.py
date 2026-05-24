from datetime import datetime, timedelta

from db import query_db, get_db


DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
INPUT_DATETIME_FORMAT = '%Y-%m-%d %H:%M'
MAX_HOURS_PER_DAY = 4
ALLOWED_DURATIONS = (1, 2, 3, 4)
CHECK_IN_GRACE_MINUTES = 30
LIVE_STATUSES = ('upcoming', 'active')


# ─── Formatting helpers ──────────────────────────────────────────────────
def _parse_booking_datetime(booking_date, start_time):
    return datetime.strptime(f'{booking_date} {start_time}', INPUT_DATETIME_FORMAT)


def _fmt(dt):
    return dt.strftime(DATETIME_FORMAT)


def _now_text():
    return _fmt(datetime.now())


def _reservation_hours(row):
    start_dt = datetime.strptime(row['startTime'], DATETIME_FORMAT)
    end_dt = datetime.strptime(row['endTime'], DATETIME_FORMAT)
    return (end_dt - start_dt).total_seconds() / 3600


# ─── Overlap / occupancy helpers ─────────────────────────────────────────
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


# ─── Zone listing ────────────────────────────────────────────────────────
def get_zones_with_seats():
    zones = query_db('SELECT * FROM zones ORDER BY zoneId')
    result = []

    for zone in zones:
        seats = query_db(
            'SELECT seatId, deskNo, status FROM seats WHERE zoneId = ? ORDER BY deskNo',
            (zone['zoneId'],),
        )
        seat_list = [dict(s) for s in seats]
        result.append({
            'zoneId':      zone['zoneId'],
            'name':        zone['name'],
            'location':    zone['location'],
            'cols':        zone['cols'],
            'zone_status': zone['status'],
            'seats':       seat_list,
            'total':       len(seat_list),
            'available':   sum(1 for s in seat_list if s['status'] == 'available'),
        })

    return result


# ─── State-sync sweeps ───────────────────────────────────────────────────
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


# ─── Availability + booking ──────────────────────────────────────────────
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


def book_seat(user_id, seat_id, booking_date, start_time, duration):
    """Reserve a seat. Returns (True, msg) or (False, err)."""
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


# ─── Reservation listing / cancel ────────────────────────────────────────
def get_user_reservations(user_id):
    update_expired_reservations()

    reservations = query_db(
        """
        SELECT
            r.reservationId,
            r.uId,
            r.seatId,
            r.startTime,
            r.endTime,
            r.status,
            s.deskNo,
            z.name AS zoneName,
            z.location,
            c.checkInId,
            c.checkInTime,
            c.status AS checkInStatus
        FROM reservations r
        JOIN seats s ON r.seatId = s.seatId
        JOIN zones z ON s.zoneId = z.zoneId
        LEFT JOIN check_in_logs c ON c.reservationId = r.reservationId
        WHERE r.uId = ?
        ORDER BY r.startTime DESC
        """,
        (user_id,),
    )
    return [dict(row) for row in reservations]


def cancel_reservation(reservation_id, user_id, is_admin=False):
    reservation = query_db(
        """
        SELECT reservationId, uId, seatId, status
        FROM reservations
        WHERE reservationId = ?
        """,
        (reservation_id,),
        one=True,
    )

    if not reservation:
        return False, 'Reservation not found.'
    if reservation['status'] not in LIVE_STATUSES:
        return False, 'Only upcoming or active reservations can be cancelled.'
    if not is_admin and reservation['uId'] != user_id:
        return False, 'You can only cancel your own reservation.'

    db = get_db()
    db.execute(
        "UPDATE reservations SET status = 'cancelled' WHERE reservationId = ?",
        (reservation_id,),
    )

    _recompute_seat_status(reservation['seatId'])

    if is_admin and reservation['uId'] != user_id:
        db.execute(
            """
            INSERT INTO admin_action_logs (userId, seatId, actionType)
            VALUES (?, ?, 'cancel_reservation')
            """,
            (user_id, reservation['seatId']),
        )

    db.commit()
    return True, 'Reservation cancelled successfully.'
