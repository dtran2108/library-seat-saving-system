"""Admin controllers — split into focused submodules.

Files:
    _common.py      — shared constants (datetime formats, limits, local TZ)
    reservations.py — override / list bookings
    seats.py        — block / unblock seats
    users.py        — list / suspend / penalty
    dashboard.py    — KPIs + chart data + alerts

All public names below are re-exported here so external callers can keep using
`from controllers.admin import X` without caring which submodule X lives in.
"""
from .reservations import (
    override_reservation,
    get_bookings_for_date,
)
from .seats import (
    block_seat,
    unblock_seat,
)
from .users import (
    list_users,
    set_user_status,
    issue_user_penalty,
    revoke_user_penalty,
)
from .dashboard import (
    get_dashboard_data,
    get_admin_kpis,
    get_hourly_bookings,
    get_metric_series,
    get_peak_hour_forecast,
    get_zone_summaries,
    recent_admin_actions,
    derive_alerts,
)

__all__ = [
    # reservations
    'override_reservation',
    'get_bookings_for_date',
    # seats
    'block_seat',
    'unblock_seat',
    # users
    'list_users',
    'set_user_status',
    'issue_user_penalty',
    'revoke_user_penalty',
    # dashboard
    'get_dashboard_data',
    'get_admin_kpis',
    'get_hourly_bookings',
    'get_metric_series',
    'get_peak_hour_forecast',
    'get_zone_summaries',
    'recent_admin_actions',
    'derive_alerts',
]
