"""Shared constants for the admin controllers package."""
from zoneinfo import ZoneInfo


DB_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT        = '%Y-%m-%d'

# Domain limits.
MAX_OVERRIDE_HOURS = 4
MAX_PENALTY_DAYS   = 365

# SQLite's CURRENT_TIMESTAMP returns UTC. The library is operated in Taiwan,
# so we convert at display time for any timestamp surfaced in the admin UI.
LOCAL_TZ = ZoneInfo('Asia/Taipei')
