"""Admin user management: list, suspend/reactivate, issue/revoke penalty."""
from datetime import date, datetime

from db import query_db, get_db

from ._common import DATE_FORMAT, MAX_PENALTY_DAYS


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
