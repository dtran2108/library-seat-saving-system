"""Reservation read + cancel. The "user views and manages their existing
reservations" side of the lifecycle."""
from db import query_db, get_db

from ._common import LIVE_STATUSES, _recompute_seat_status
from .state import update_expired_reservations


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
