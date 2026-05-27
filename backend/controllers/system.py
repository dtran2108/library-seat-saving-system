"""System-wide settings (key/value store) used for runtime toggles like the
booking-system kill switch.

Lives in its own module so both controllers/seats.py (enforcement) and
controllers/admin.py (toggle) can import it without creating a cycle.
"""
from db import query_db, get_db


BOOKING_ENABLED_KEY = 'booking_enabled'
DEFAULT_BOOKING_ENABLED = True


def _ensure_settings_table():
    """CREATE TABLE IF NOT EXISTS so existing databases that pre-date this
    table get it on first access."""
    get_db().execute(
        """
        CREATE TABLE IF NOT EXISTS system_settings (
            skey      TEXT PRIMARY KEY,
            svalue    TEXT NOT NULL,
            updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updatedBy TEXT,
            FOREIGN KEY (updatedBy) REFERENCES users(uId)
        )
        """
    )


def is_booking_enabled():
    """Return whether the booking system is currently accepting new bookings."""
    _ensure_settings_table()
    row = query_db(
        'SELECT svalue FROM system_settings WHERE skey = ?',
        (BOOKING_ENABLED_KEY,),
        one=True,
    )
    if row is None:
        return DEFAULT_BOOKING_ENABLED
    return row['svalue'] == 'true'


def set_booking_enabled(enabled, admin_user_id):
    """Toggle the booking system on/off. Returns (success, message)."""
    _ensure_settings_table()
    value = 'true' if enabled else 'false'
    db = get_db()
    db.execute(
        """
        INSERT INTO system_settings (skey, svalue, updatedBy)
        VALUES (?, ?, ?)
        ON CONFLICT(skey) DO UPDATE SET
            svalue    = excluded.svalue,
            updatedAt = CURRENT_TIMESTAMP,
            updatedBy = excluded.updatedBy
        """,
        (BOOKING_ENABLED_KEY, value, admin_user_id),
    )
    db.commit()
    return True, f'Booking system {"enabled" if enabled else "disabled"}.'
