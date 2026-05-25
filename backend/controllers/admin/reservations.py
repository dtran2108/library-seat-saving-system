"""Admin operations on individual reservations (override + listing by date)."""
from datetime import datetime, timedelta

from db import query_db, get_db
from controllers.seats import update_expired_reservations

from ._common import DB_DATETIME_FORMAT, MAX_OVERRIDE_HOURS


def override_reservation(reservation_id, admin_user_id, start_time, duration):
    """Admin: move an upcoming/active reservation to a new time on the same
    date and seat. Returns (True, msg) on success or (False, err) on failure.
    """
    try:
        reservation_id = int(reservation_id)
    except (TypeError, ValueError):
        return False, 'Invalid reservation ID.'

    try:
        duration = int(duration)
        if duration < 1 or duration > MAX_OVERRIDE_HOURS:
            return False, f'Duration must be between 1 and {MAX_OVERRIDE_HOURS} hours.'
    except (TypeError, ValueError):
        return False, 'Invalid duration.'

    reservation = query_db(
        """
        SELECT reservationId, uId, seatId, startTime, endTime, status
        FROM reservations
        WHERE reservationId = ?
        """,
        (reservation_id,),
        one=True
    )

    if not reservation:
        return False, 'Reservation not found.'

    if reservation['status'] not in ('upcoming', 'active'):
        return False, 'Only upcoming or active reservations can be overridden.'

    # Keep the booking on its original date — only the time-of-day moves.
    try:
        original_start = datetime.strptime(reservation['startTime'], DB_DATETIME_FORMAT)
        booking_date = original_start.strftime('%Y-%m-%d')
        new_start = datetime.strptime(f'{booking_date} {start_time}', '%Y-%m-%d %H:%M')
    except (TypeError, ValueError):
        return False, 'Invalid start time.'

    new_end = new_start + timedelta(hours=duration)
    new_start_text = new_start.strftime(DB_DATETIME_FORMAT)
    new_end_text   = new_end.strftime(DB_DATETIME_FORMAT)

    if new_start_text == reservation['startTime'] and new_end_text == reservation['endTime']:
        return False, 'New time is the same as the current reservation.'

    seat_conflict = query_db(
        """
        SELECT reservationId
        FROM reservations
        WHERE seatId = ?
        AND reservationId != ?
        AND status IN ('upcoming', 'active')
        AND startTime < ?
        AND endTime > ?
        """,
        (reservation['seatId'], reservation_id, new_end_text, new_start_text),
        one=True
    )

    if seat_conflict:
        return False, 'The new time conflicts with another reservation on this seat.'

    db = get_db()
    now = datetime.now()
    now_text = now.strftime(DB_DATETIME_FORMAT)

    # Recompute reservation status based on the new window.
    if new_start <= now < new_end:
        new_status = 'active'
    elif new_start > now:
        new_status = 'upcoming'
    else:
        new_status = 'completed'

    db.execute(
        """
        UPDATE reservations
        SET startTime = ?, endTime = ?, status = ?
        WHERE reservationId = ?
        """,
        (new_start_text, new_end_text, new_status, reservation_id)
    )

    # Recompute the seat's status: occupied iff there is now an active
    # reservation covering the current moment.
    active_now = query_db(
        """
        SELECT reservationId
        FROM reservations
        WHERE seatId = ?
        AND status = 'active'
        AND startTime <= ?
        AND endTime > ?
        """,
        (reservation['seatId'], now_text, now_text),
        one=True
    )

    db.execute(
        """
        UPDATE seats
        SET status = ?
        WHERE seatId = ?
        AND status != 'blocked'
        """,
        ('occupied' if active_now else 'available', reservation['seatId'])
    )

    db.execute(
        """
        INSERT INTO admin_action_logs (userId, seatId, actionType)
        VALUES (?, ?, 'modify_reservation')
        """,
        (admin_user_id, reservation['seatId'])
    )

    db.commit()
    return True, 'Reservation time overridden.'


def get_bookings_for_date(booking_date):
    """Return every reservation that overlaps the given YYYY-MM-DD date."""
    try:
        datetime.strptime(booking_date, '%Y-%m-%d')
    except (TypeError, ValueError):
        return False, 'Invalid date.'

    # Refresh statuses so 'upcoming' rolls over to 'active'/'completed' before
    # we display them — keeps the override button accurate.
    update_expired_reservations()

    start_of_day = f'{booking_date} 00:00:00'
    end_of_day   = f'{booking_date} 23:59:59'

    rows = query_db(
        """
        SELECT
            r.reservationId,
            r.uId,
            r.seatId,
            r.startTime,
            r.endTime,
            r.status,
            u.uname,
            s.deskNo,
            z.name AS zoneName
        FROM reservations r
        JOIN users u ON r.uId    = u.uId
        JOIN seats s ON r.seatId = s.seatId
        JOIN zones z ON s.zoneId = z.zoneId
        WHERE r.startTime <= ?
          AND r.endTime   >= ?
        ORDER BY r.startTime
        """,
        (end_of_day, start_of_day)
    )

    bookings = []
    for row in rows:
        start = datetime.strptime(row['startTime'], DB_DATETIME_FORMAT)
        end   = datetime.strptime(row['endTime'],   DB_DATETIME_FORMAT)
        bookings.append({
            'reservationId': row['reservationId'],
            'seat_label':    f"{row['zoneName']} · {row['deskNo']}",
            'user_label':    f"{row['uname']} ({row['uId']})",
            'booking_date':  start.strftime('%Y-%m-%d'),
            'start_time':    start.strftime('%H:%M'),
            'end_time':      end.strftime('%H:%M'),
            'duration':      int((end - start).total_seconds() // 3600),
            'status':        row['status'],
        })
    return True, bookings
