from db import query_db, get_zones_with_seats


def get_dashboard_data():
    """Return zones list and seat summary stats for the admin dashboard."""
    zones = get_zones_with_seats()
    # One query instead of looping over zones — much faster with many zones.
    stats = query_db(
        '''SELECT COUNT(*) AS total,
                  SUM(CASE WHEN status = "maintenance" THEN 1 ELSE 0 END) AS blocked
           FROM seats''',
        one=True
    )
    total_seats   = stats['total']   or 0
    blocked_seats = stats['blocked'] or 0
    return zones, total_seats, blocked_seats
