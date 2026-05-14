from datetime import datetime, timedelta
from db import query_db, get_db

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

    seat = query_db('SELECT seatId, status FROM seats WHERE seatId = ?', (seat_id,), one=True)
    if not seat:
        return False, 'Seat not found.'
    if seat['status'] != 'available':
        return False, 'This seat is no longer available.'

    db = get_db()
    # Atomic update: only succeeds if no one else claimed the seat between the
    # read above and now. rowcount == 0 means another request won the race.
    cur = db.execute(
        "UPDATE seats SET status = 'booked' WHERE seatId = ? AND status = 'available'",
        (seat_id,)
    )
    if cur.rowcount == 0:
        return False, 'This seat was just taken. Please choose another.'

    db.execute(
        'INSERT INTO reservations (uId, seatId, startTime, endTime, status) VALUES (?, ?, ?, ?, ?)',
        (
            user_id,
            seat_id,
            start_dt.strftime('%Y-%m-%d %H:%M:%S'),
            end_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'active',
        )
    )
    db.commit()
    return True, 'Seat booked successfully!'
