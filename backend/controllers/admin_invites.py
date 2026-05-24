"""Admin signup-by-invitation flow.

An existing admin issues a single-use, time-limited invite for a specific
Student ID. The invitee opens the tokenized link, picks their own password,
and the consumption step creates the `admin` user atomically.
"""
import secrets
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from db import query_db, get_db


INVITE_TTL_DAYS = 7
DB_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def _ensure_invites_table():
    """CREATE TABLE IF NOT EXISTS so existing DBs migrate transparently."""
    get_db().execute(
        """
        CREATE TABLE IF NOT EXISTS admin_invites (
            inviteId   INTEGER PRIMARY KEY AUTOINCREMENT,
            token      TEXT NOT NULL UNIQUE,
            uId        TEXT NOT NULL,
            uname      TEXT NOT NULL,
            phoneNo    TEXT,
            createdBy  TEXT NOT NULL,
            createdAt  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expiresAt  DATETIME NOT NULL,
            usedAt     DATETIME,
            usedBy     TEXT,
            revokedAt  DATETIME,
            revokedBy  TEXT,
            FOREIGN KEY (createdBy) REFERENCES users(uId)
        )
        """
    )


def _fmt(dt):
    return dt.strftime(DB_DATETIME_FORMAT)


def create_invite(target_uid, target_name, phone_no, admin_user_id):
    """Issue an invite for `target_uid`. Returns (success, dict_or_msg)."""
    target_uid  = (target_uid or '').strip()
    target_name = (target_name or '').strip()
    phone_no    = (phone_no or '').strip() or None

    if not target_uid:
        return False, 'Student ID is required.'
    if len(target_uid) < 6:
        return False, 'Student ID must be at least 6 characters.'
    if not target_name:
        return False, 'Full name is required.'
    if len(target_name) > 100:
        return False, 'Full name must be 100 characters or fewer.'

    _ensure_invites_table()

    if query_db('SELECT uId FROM users WHERE uId = ?', (target_uid,), one=True):
        return False, 'An account with this Student ID already exists.'

    existing = query_db(
        """
        SELECT inviteId FROM admin_invites
        WHERE uId = ?
        AND usedAt    IS NULL
        AND revokedAt IS NULL
        AND expiresAt > ?
        """,
        (target_uid, _fmt(datetime.now())),
        one=True,
    )
    if existing:
        return False, 'A pending invite already exists for this Student ID.'

    token      = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=INVITE_TTL_DAYS)

    db = get_db()
    cur = db.execute(
        """
        INSERT INTO admin_invites (token, uId, uname, phoneNo, createdBy, expiresAt)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (token, target_uid, target_name, phone_no, admin_user_id, _fmt(expires_at)),
    )
    db.commit()

    return True, {
        'inviteId':  cur.lastrowid,
        'token':     token,
        'uId':       target_uid,
        'uname':     target_name,
        'phoneNo':   phone_no,
        'expiresAt': _fmt(expires_at),
    }


def list_pending_invites():
    """Return all non-consumed, non-revoked, non-expired invites."""
    _ensure_invites_table()
    return [dict(r) for r in query_db(
        """
        SELECT inviteId, token, uId, uname, phoneNo, createdBy, createdAt, expiresAt
        FROM admin_invites
        WHERE usedAt    IS NULL
        AND   revokedAt IS NULL
        AND   expiresAt > ?
        ORDER BY createdAt DESC
        """,
        (_fmt(datetime.now()),),
    )]


def revoke_invite(invite_id, admin_user_id):
    """Revoke a pending invite. Returns (success, msg)."""
    try:
        invite_id = int(invite_id)
    except (TypeError, ValueError):
        return False, 'Invalid invite ID.'

    _ensure_invites_table()
    invite = query_db(
        'SELECT inviteId, usedAt, revokedAt FROM admin_invites WHERE inviteId = ?',
        (invite_id,),
        one=True,
    )
    if not invite:
        return False, 'Invite not found.'
    if invite['usedAt']:
        return False, 'Invite was already used.'
    if invite['revokedAt']:
        return False, 'Invite is already revoked.'

    db = get_db()
    db.execute(
        'UPDATE admin_invites SET revokedAt = ?, revokedBy = ? WHERE inviteId = ?',
        (_fmt(datetime.now()), admin_user_id, invite_id),
    )
    db.commit()
    return True, 'Invite revoked.'


def find_invite_by_token(token):
    """Look up a usable invite by token. Returns the invite row dict or None
    along with a reason string ('ok' or one of: 'missing', 'used', 'revoked',
    'expired'). The reason lets the signup page show a precise error."""
    token = (token or '').strip()
    if not token:
        return None, 'missing'

    _ensure_invites_table()
    row = query_db(
        """
        SELECT inviteId, token, uId, uname, phoneNo, expiresAt, usedAt, revokedAt
        FROM admin_invites
        WHERE token = ?
        """,
        (token,),
        one=True,
    )
    if not row:
        return None, 'missing'
    if row['usedAt']:
        return None, 'used'
    if row['revokedAt']:
        return None, 'revoked'
    if row['expiresAt'] <= _fmt(datetime.now()):
        return None, 'expired'
    return dict(row), 'ok'


def consume_invite(token, password):
    """Validate the token, create the admin user, mark the invite used.
    Returns (success, user_row_or_msg)."""
    invite, reason = find_invite_by_token(token)
    if not invite:
        messages = {
            'missing':  'This invite link is invalid.',
            'used':     'This invite has already been used.',
            'revoked':  'This invite was revoked by an admin.',
            'expired':  'This invite has expired. Ask an admin for a new one.',
        }
        return False, messages.get(reason, 'Invalid invite.')

    if not password or len(password) < 6:
        return False, 'Password must be at least 6 characters.'

    # Final race-condition guard: someone may have signed up between issue and
    # consumption.
    if query_db('SELECT uId FROM users WHERE uId = ?', (invite['uId'],), one=True):
        return False, 'An account with this Student ID already exists.'

    db = get_db()
    db.execute(
        """
        INSERT INTO users (uId, uname, phoneNo, password, role, ustatus)
        VALUES (?, ?, ?, ?, 'admin', 'active')
        """,
        (invite['uId'], invite['uname'], invite['phoneNo'], generate_password_hash(password)),
    )
    db.execute(
        'UPDATE admin_invites SET usedAt = ?, usedBy = ? WHERE inviteId = ?',
        (_fmt(datetime.now()), invite['uId'], invite['inviteId']),
    )
    db.commit()

    return True, {'uId': invite['uId'], 'uname': invite['uname']}
