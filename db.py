"""
db.py — SQLite database helpers for the Library Seat Saving System.

Provides:
    get_db()              — get (or open) the per-request SQLite connection
    close_db()            — teardown handler registered with app.teardown_appcontext
    query_db()            — SELECT helper returning sqlite3.Row object(s)
    init_db()             — create all tables from schema.sql (safe to re-run)
    get_zones_with_seats() — build the full zone+seat list used by seat-map routes
"""

import os
import sqlite3

from flask import current_app, g


def get_db():
    """
    Return the SQLite connection for this request.

    Opens a new connection the first time it is called within a request
    context and caches it in Flask's `g` object so subsequent calls within
    the same request reuse the same connection.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row   # allows dict-style column access
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(e=None):
    """Close the SQLite connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    """
    Execute a SELECT query and return row(s) as sqlite3.Row objects.

    Args:
        query: SQL SELECT statement with ? placeholders.
        args:  values to bind to the placeholders.
        one:   if True, return a single row (or None); otherwise a list.
    """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def init_db():
    """
    Initialize the database by executing schema.sql.

    Uses IF NOT EXISTS everywhere, so it is safe to call on every startup.
    Must be called inside an application context.
    """
    db = get_db()
    schema_path = os.path.join(current_app.root_path, 'schema.sql')
    with open(schema_path, 'r') as f:
        db.executescript(f.read())
    db.commit()


def get_zones_with_seats():
    """
    Build the full zone list, each entry containing its seats.

    Returns a list of dicts with keys:
        zoneId, name, location, cols, zone_status,
        seats     — list of seat dicts (seatId, destNo, status)
        total     — total seat count in the zone
        available — count of seats whose status is 'available'
    """
    zones = query_db('SELECT * FROM zones ORDER BY zoneId')
    result = []
    for zone in zones:
        seats = query_db(
            'SELECT seatId, destNo, status FROM seats WHERE zoneId = ? ORDER BY destNo',
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
