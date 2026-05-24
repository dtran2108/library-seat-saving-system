from datetime import date, datetime, timedelta

from db import query_db, get_db
from controllers.seats import get_zones_with_seats, update_expired_reservations


DB_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'
MAX_OVERRIDE_HOURS = 4
MAX_PENALTY_DAYS = 365


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


def get_dashboard_data():
    """Return zones list and seat summary stats for the admin dashboard."""
    zones = get_zones_with_seats()
    # One query instead of looping over zones — much faster with many zones.
    stats = query_db(
        '''SELECT COUNT(*) AS total,
                  SUM(CASE WHEN status = "blocked" THEN 1 ELSE 0 END) AS blocked
           FROM seats''',
        one=True
    )
    total_seats   = stats['total']   or 0
    blocked_seats = stats['blocked'] or 0
    return zones, total_seats, blocked_seats


def block_seat(seat_id, admin_user_id):
    """Mark a seat as 'blocked' for maintenance.

    Refuses if the seat is already blocked or has any upcoming/active
    reservation — the admin must override those first.
    """
    try:
        seat_id = int(seat_id)
    except (TypeError, ValueError):
        return False, 'Invalid seat ID.'

    seat = query_db(
        'SELECT seatId, status FROM seats WHERE seatId = ?',
        (seat_id,),
        one=True
    )

    if not seat:
        return False, 'Seat not found.'

    if seat['status'] == 'blocked':
        return False, 'This seat is already blocked.'

    active_booking = query_db(
        """
        SELECT reservationId
        FROM reservations
        WHERE seatId = ?
        AND status IN ('upcoming', 'active')
        """,
        (seat_id,),
        one=True
    )

    if active_booking:
        return False, 'Cancel the seat\'s upcoming or active reservations before blocking it.'

    db = get_db()
    db.execute(
        "UPDATE seats SET status = 'blocked' WHERE seatId = ?",
        (seat_id,)
    )
    db.execute(
        """
        INSERT INTO admin_action_logs (userId, seatId, actionType)
        VALUES (?, ?, 'block_seat')
        """,
        (admin_user_id, seat_id)
    )
    db.commit()
    return True, 'Seat blocked for maintenance.'


def unblock_seat(seat_id, admin_user_id):
    """Restore a 'blocked' seat to 'available'."""
    try:
        seat_id = int(seat_id)
    except (TypeError, ValueError):
        return False, 'Invalid seat ID.'

    seat = query_db(
        'SELECT seatId, status FROM seats WHERE seatId = ?',
        (seat_id,),
        one=True
    )

    if not seat:
        return False, 'Seat not found.'

    if seat['status'] != 'blocked':
        return False, 'This seat is not currently blocked.'

    db = get_db()
    db.execute(
        "UPDATE seats SET status = 'available' WHERE seatId = ?",
        (seat_id,)
    )
    db.execute(
        """
        INSERT INTO admin_action_logs (userId, seatId, actionType)
        VALUES (?, ?, 'unblock_seat')
        """,
        (admin_user_id, seat_id)
    )
    db.commit()
    return True, 'Seat unblocked and available again.'


# ─── User management ────────────────────────────────────────────────────
def _expire_past_penalties():
    """Mark any active penalty whose endDate has passed as 'expired'."""
    get_db().execute(
        """
        UPDATE penalties
        SET status = 'expired'
        WHERE status = 'active'
        AND endDate < ?
        """,
        (date.today().strftime(DATE_FORMAT),),
    )
    get_db().commit()


def list_users():
    """Return all users with their current active penalty (if any) and basic
    booking stats. Admins come first, then by name."""
    _expire_past_penalties()

    rows = query_db(
        """
        SELECT
            u.uId,
            u.uname,
            u.phoneNo,
            u.role,
            u.ustatus,
            p.penaltyId       AS active_penalty_id,
            p.reason          AS active_penalty_reason,
            p.startDate       AS active_penalty_start,
            p.endDate         AS active_penalty_end,
            (SELECT COUNT(*) FROM reservations r WHERE r.uId = u.uId)                          AS bookings_count,
            (SELECT COUNT(*) FROM reservations r WHERE r.uId = u.uId AND r.status = 'no_show') AS no_show_count
        FROM users u
        LEFT JOIN penalties p
            ON p.reservationId IN (SELECT reservationId FROM reservations WHERE uId = u.uId)
            AND p.status = 'active'
        ORDER BY (u.role = 'admin') DESC, u.uname
        """,
    )

    # SQLite returns one row per matching penalty; we want one row per user.
    # Dedup keeping the first active penalty (if any).
    seen = {}
    for row in rows:
        if row['uId'] not in seen:
            seen[row['uId']] = dict(row)
    return list(seen.values())


def _get_user(target_user_id):
    return query_db('SELECT uId, uname, role, ustatus FROM users WHERE uId = ?', (target_user_id,), one=True)


def set_user_status(target_user_id, admin_user_id, new_status):
    """Suspend or reactivate a user. new_status must be 'active' or 'suspended'."""
    if new_status not in ('active', 'suspended'):
        return False, 'Invalid status.'
    if target_user_id == admin_user_id:
        return False, 'You cannot change your own status.'

    user = _get_user(target_user_id)
    if not user:
        return False, 'User not found.'

    if user['ustatus'] == new_status:
        return False, f'User is already {new_status}.'

    db = get_db()
    db.execute(
        'UPDATE users SET ustatus = ? WHERE uId = ?',
        (new_status, target_user_id),
    )

    action = 'suspend_user' if new_status == 'suspended' else 'reactivate_user'
    db.execute(
        "INSERT INTO admin_action_logs (userId, actionType) VALUES (?, ?)",
        (admin_user_id, action),
    )
    db.commit()

    verb = 'suspended' if new_status == 'suspended' else 'reactivated'
    return True, f'{user["uname"]} {verb}.'


def issue_user_penalty(target_user_id, admin_user_id, reason, end_date):
    """Issue an active penalty against a user, ending on `end_date` (YYYY-MM-DD).
    Refuses if the user already has an active penalty."""
    if target_user_id == admin_user_id:
        return False, 'You cannot issue a penalty against yourself.'

    reason = (reason or '').strip()
    if not reason:
        return False, 'A reason is required.'
    if len(reason) > 280:
        return False, 'Reason must be 280 characters or fewer.'

    try:
        end = datetime.strptime(end_date, DATE_FORMAT).date()
    except (TypeError, ValueError):
        return False, 'Invalid end date (expected YYYY-MM-DD).'

    today = date.today()
    if end < today:
        return False, 'End date must be today or in the future.'
    if (end - today).days > MAX_PENALTY_DAYS:
        return False, f'Penalty cannot exceed {MAX_PENALTY_DAYS} days.'

    user = _get_user(target_user_id)
    if not user:
        return False, 'User not found.'

    _expire_past_penalties()
    existing = query_db(
        """
        SELECT p.penaltyId
        FROM penalties p
        JOIN reservations r ON r.reservationId = p.reservationId
        WHERE r.uId = ?
        AND p.status = 'active'
        """,
        (target_user_id,),
        one=True,
    )
    if existing:
        return False, 'This user already has an active penalty. Revoke it first.'

    # Pin the penalty to the user's most recent reservation, if any. The
    # penalties.reservationId column is required for the link-back to a user
    # to work via the schema's existing FK.
    last_reservation = query_db(
        """
        SELECT reservationId
        FROM reservations
        WHERE uId = ?
        ORDER BY createdAt DESC
        LIMIT 1
        """,
        (target_user_id,),
        one=True,
    )
    if not last_reservation:
        return False, 'User has no reservations to attach a penalty to yet.'

    db = get_db()
    cur = db.execute(
        """
        INSERT INTO penalties (reservationId, reason, startDate, endDate, status)
        VALUES (?, ?, ?, ?, 'active')
        """,
        (last_reservation['reservationId'], reason, today.strftime(DATE_FORMAT), end.strftime(DATE_FORMAT)),
    )
    penalty_id = cur.lastrowid
    db.execute(
        "INSERT INTO admin_action_logs (userId, penaltyId, actionType) VALUES (?, ?, 'issue_penalty')",
        (admin_user_id, penalty_id),
    )
    db.commit()
    return True, f'Penalty issued until {end.strftime(DATE_FORMAT)}.'


def revoke_user_penalty(penalty_id, admin_user_id):
    """Revoke an active penalty by id."""
    try:
        penalty_id = int(penalty_id)
    except (TypeError, ValueError):
        return False, 'Invalid penalty ID.'

    penalty = query_db(
        'SELECT penaltyId, status FROM penalties WHERE penaltyId = ?',
        (penalty_id,),
        one=True,
    )
    if not penalty:
        return False, 'Penalty not found.'
    if penalty['status'] != 'active':
        return False, f'Penalty is already {penalty["status"]}.'

    db = get_db()
    db.execute(
        "UPDATE penalties SET status = 'revoked' WHERE penaltyId = ?",
        (penalty_id,),
    )
    db.execute(
        "INSERT INTO admin_action_logs (userId, penaltyId, actionType) VALUES (?, ?, 'revoke_penalty')",
        (admin_user_id, penalty_id),
    )
    db.commit()
    return True, 'Penalty revoked.'
