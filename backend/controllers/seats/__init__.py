"""User-side seat controllers — split into focused submodules.

Files:
    _common.py       — constants + formatting/validation/overlap helpers
    zones.py         — seat-map listing
    state.py         — timed sweeps + check-in (lifecycle transitions)
    booking.py       — availability search + create reservation
    reservations.py  — list + cancel a user's reservations

All public names below are re-exported here so external callers can keep using
`from controllers.seats import X` without caring which submodule X lives in.
"""
from ._common import CHECK_IN_GRACE_MINUTES
from .zones import get_zones_with_seats
from .state import (
    update_expired_reservations,
    sweep_missed_check_ins,
    check_in_reservation,
)
from .booking import (
    get_available_seats,
    book_seat,
)
from .reservations import (
    get_user_reservations,
    cancel_reservation,
)

__all__ = [
    # constants
    'CHECK_IN_GRACE_MINUTES',
    # zones
    'get_zones_with_seats',
    # state
    'update_expired_reservations',
    'sweep_missed_check_ins',
    'check_in_reservation',
    # booking
    'get_available_seats',
    'book_seat',
    # reservations
    'get_user_reservations',
    'cancel_reservation',
]
