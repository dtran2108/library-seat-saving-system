from datetime import datetime, timedelta
from db import query_db, get_db
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
INPUT_DATETIME_FORMAT = '%Y-%m-%d %H:%M'
MAX_HOURS_PER_DAY = 4


def _parse_booking_datetime(booking_date, start_time):
    return datetime.strptime(f'{booking_date} {start_time}', INPUT_DATETIME_FORMAT)


def _format_datetime(dt):
    return dt.strftime(DATETIME_FORMAT)


def _reservation_hours(row):
    start_dt = datetime.strptime(row['startTime'], DATETIME_FORMAT)
    end_dt = datetime.strptime(row['endTime'], DATETIME_FORMAT)
    return (end_dt - start_dt).total_seconds() / 3600


def get_zones_with_seats():
    zones = query_db('SELECT * FROM zones ORDER BY zoneId')
    result = []
    for zone in zones:
        seats = query_db(
            'SELECT seatId, destNo, status FROM seats WHERE zoneId = ? ORDER BY destNo',
            (zone['zoneId'],),
        )
        # Convert sqlite3.Row objects to plain dicts so Jinja2 templates can
        # access them with dot notation and dict syntax interchangeably.
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

def get_seat_map_data():
    return get_zones_with_seats()

def update_expired_reservations():
    """Update reservation and seat statuses based on current time."""
    now = datetime.now()
    now_text = _format_datetime(now)
    db = get_db()

    db.execute(
        """
        UPDATE reservations
        SET status = 'completed'
        WHERE status = 'active'
        AND endTime <= ?
        """,
        (now_text,)
    )

    db.execute(
        """
        UPDATE seats
        SET status = 'available'
        WHERE status = 'booked'
        AND seatId NOT IN (
            SELECT seatId
            FROM reservations
            WHERE status = 'active'
            AND startTime <= ?
            AND endTime > ?
        )
        """,
        (now_text, now_text)
    )

    db.execute(
        """
        UPDATE seats
        SET status = 'booked'
        WHERE seatId IN (
            SELECT seatId
            FROM reservations
            WHERE status = 'active'
            AND startTime <= ?
            AND endTime > ?
        )
        """,
        (now_text, now_text)
    )

    db.commit()


def get_available_seats(booking_date, start_time, duration, zone_id=None):
    """Return seats available for the requested time range."""
    if not all([booking_date, start_time, duration]):
        return False, 'booking_date, start_time, and duration are required.'

    try:
        duration = int(duration)
        if duration < 1 or duration > MAX_HOURS_PER_DAY:
            return False, f'Duration must be between 1 and {MAX_HOURS_PER_DAY} hours.'
        start_dt = _parse_booking_datetime(booking_date, start_time)
    except ValueError:
        return False, 'Invalid date, time, or duration.'

    end_dt = start_dt + timedelta(hours=duration)
    start_text = _format_datetime(start_dt)
    end_text = _format_datetime(end_dt)

    params = [end_text, start_text]
    zone_filter = ''

    if zone_id:
        try:
            zone_id = int(zone_id)
        except ValueError:
            return False, 'Invalid zone ID.'

        zone_filter = 'AND s.zoneId = ?'
        params.append(zone_id)

    seats = query_db(
        f"""
        SELECT s.seatId, s.destNo, s.status, s.zoneId, z.name AS zoneName
        FROM seats s
        JOIN zones z ON s.zoneId = z.zoneId
        WHERE s.status != 'maintenance'
        AND z.status != 'maintenance'
        AND s.seatId NOT IN (
            SELECT r.seatId
            FROM reservations r
            WHERE r.status = 'active'
            AND r.startTime < ?
            AND r.endTime > ?
        )
        {zone_filter}
        ORDER BY z.zoneId, s.destNo
        """,
        tuple(params)
    )

    return True, [dict(seat) for seat in seats]

def _get_user_daily_hours(user_id, booking_date):
    start_of_day = f'{booking_date} 00:00:00'
    end_of_day = f'{booking_date} 23:59:59'

    reservations = query_db(
        """
        SELECT startTime, endTime
        FROM reservations
        WHERE uId = ?
        AND status = 'active'
        AND startTime >= ?
        AND startTime <= ?
        """,
        (user_id, start_of_day, end_of_day)
    )

    return sum(_reservation_hours(row) for row in reservations)


def book_seat(user_id, seat_id, booking_date, start_time, duration):
    """Reserve a seat atomically. Returns (True, success_msg) or (False, error_msg)."""
    if not all([seat_id, booking_date, start_time, duration]):
        return False, 'All fields are required.'

    try:
        seat_id  = int(seat_id)
        duration = int(duration)
        if duration not in (1, 2, 3, 4):
            raise ValueError
    except ValueError:
        return False, 'Invalid seat ID or duration.'

    try:
        start_dt = datetime.strptime(f'{booking_date} {start_time}', '%Y-%m-%d %H:%M')
    except ValueError:
        return False, 'Invalid date or time format.'

    end_dt = start_dt + timedelta(hours=duration)
    
    start_text = _format_datetime(start_dt)
    end_text = _format_datetime(end_dt)

    if duration > MAX_HOURS_PER_DAY:
        return False, f'You can book at most {MAX_HOURS_PER_DAY} hours per day.'

    user_daily_hours = _get_user_daily_hours(user_id, booking_date)
    if user_daily_hours + duration > MAX_HOURS_PER_DAY:
        return False, f'You can book at most {MAX_HOURS_PER_DAY} hours per day.'
        

    seat = query_db(
        """
        SELECT s.seatId, s.status, z.status AS zone_status
        FROM seats s
        JOIN zones z ON s.zoneId = z.zoneId
        WHERE s.seatId = ?
        """,
        (seat_id,),
        one=True
    )

    if not seat:
        return False, 'Seat not found.'

    if seat['status'] == 'maintenance' or seat['zone_status'] == 'maintenance':
        return False, 'This seat is under maintenance.'

    seat_conflict = query_db(
        """
        SELECT rId
        FROM reservations
        WHERE seatId = ?
        AND status = 'active'
        AND startTime < ?
        AND endTime > ?
        """,
        (seat_id, end_text, start_text),
        one=True
    )

    if seat_conflict:
        return False, 'This seat is already booked during that time.'

    user_conflict = query_db(
        """
        SELECT rId
        FROM reservations
        WHERE uId = ?
        AND status = 'active'
        AND startTime < ?
        AND endTime > ?
        """,
        (user_id, end_text, start_text),
        one=True
    )

    if user_conflict:
        return False, 'You already have a booking during that time.'

    db = get_db()


    db.execute(
        'INSERT INTO reservations (uId, seatId, startTime, endTime, status) VALUES (?, ?, ?, ?, ?)',
        (
            user_id,
            seat_id,
            start_text,
            end_text,
            'active',
        )
    )

    now = datetime.now()
    if start_dt <= now < end_dt:
        db.execute(
            "UPDATE seats SET status = 'booked' WHERE seatId = ?",
            (seat_id,)
        )

    def get_user_reservations(user_id):
    update_expired_reservations()

    reservations = query_db(
        """
        SELECT
            r.rId,
            r.uId,
            r.seatId,
            r.startTime,
            r.endTime,
            r.status,
            s.destNo,
            z.name AS zoneName,
            z.location
        FROM reservations r
        JOIN seats s ON r.seatId = s.seatId
        JOIN zones z ON s.zoneId = z.zoneId
        WHERE r.uId = ?
        ORDER BY r.startTime DESC
        """,
        (user_id,)
    )

    return [dict(row) for row in reservations]


def cancel_reservation(reservation_id, user_id, is_admin=False):
    reservation = query_db(
        """
        SELECT rId, uId, seatId, status
        FROM reservations
        WHERE rId = ?
        """,
        (reservation_id,),
        one=True
    )

    if not reservation:
        return False, 'Reservation not found.'

    if reservation['status'] != 'active':
        return False, 'Only active reservations can be cancelled.'

    if not is_admin and reservation['uId'] != user_id:
        return False, 'You can only cancel your own reservation.'

    db = get_db()

    db.execute(
        """
        UPDATE reservations
        SET status = 'cancelled'
        WHERE rId = ?
        """,
        (reservation_id,)
    )

    now_text = _format_datetime(datetime.now())

    active_now = query_db(
        """
        SELECT rId
        FROM reservations
        WHERE seatId = ?
        AND status = 'active'
        AND startTime <= ?
        AND endTime > ?
        """,
        (reservation['seatId'], now_text, now_text),
        one=True
    )

    if not active_now:
        db.execute(
            """
            UPDATE seats
            SET status = 'available'
            WHERE seatId = ?
            AND status != 'maintenance'
            """,
            (reservation['seatId'],)
        )

    db.commit()
    return True, 'Reservation cancelled successfully.'

        
    db.commit()
    return True, 'Seat booked successfully!'
