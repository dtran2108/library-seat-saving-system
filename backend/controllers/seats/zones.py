"""Zone + seat listing — the data behind the seat map."""
from db import query_db


def get_zones_with_seats():
    zones = query_db('SELECT * FROM zones ORDER BY zoneId')
    result = []

    for zone in zones:
        seats = query_db(
            'SELECT seatId, deskNo, status FROM seats WHERE zoneId = ? ORDER BY deskNo',
            (zone['zoneId'],),
        )
        seat_list = [dict(s) for s in seats]
        result.append({
            'zoneId':      zone['zoneId'],
            'name':        zone['name'],
            'location':    zone['location'],
            'cols':        zone['cols'],
            'zone_status': zone['status'],
            'seats':       seat_list,
            'total':       len(seat_list),
            'available':   sum(1 for s in seat_list if s['status'] == 'available'),
        })

    return result
