from db import query_db, get_db
from controllers.seats import get_zones_with_seats


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
