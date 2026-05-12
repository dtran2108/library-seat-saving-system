"""
db.py — SQLite database connection helpers for the Library Seat Saving System.

Provides:
    get_db()    — get (or open) the per-request SQLite connection stored in Flask's g
    close_db()  — teardown handler: close the connection at the end of each request
    query_db()  — execute a SELECT and return row(s) as dict-like sqlite3.Row objects
    init_db()   — create all tables from schema.sql (safe to call multiple times)

Usage in main.py:
    from db import get_db, close_db, query_db, init_db
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
"""

import os
import sqlite3

from flask import g

# Path to the SQLite database file — stored at the project root.
DATABASE = os.path.join(os.path.dirname(__file__), 'library.db')


def get_db():
    """
    Return the SQLite connection for this request.

    Opens a new connection the first time it is called within a request
    context and caches it in Flask's `g` object so subsequent calls within
    the same request reuse the same connection.

    Returns:
        sqlite3.Connection with row_factory set to sqlite3.Row so columns
        can be accessed by name (e.g. row['uname']) as well as by index.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row   # allows dict-style column access
        g.db.execute('PRAGMA foreign_keys = ON')  # enforce FK constraints
    return g.db


def close_db(e=None):
    """
    Close the SQLite connection at the end of the request.

    Registered with app.teardown_appcontext(close_db) in main.py so Flask
    calls this automatically after every request (or app-context pop).

    Args:
        e: optional exception passed by Flask's teardown mechanism (ignored).
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    """
    Execute a SELECT query and return the result as sqlite3.Row object(s).

    Args:
        query (str): SQL SELECT statement with ? placeholders.
        args  (tuple): values to bind to the placeholders.
        one   (bool): if True, return a single row (or None if no rows);
                      if False, return a list of all rows.

    Returns:
        sqlite3.Row | None  when one=True
        list[sqlite3.Row]   when one=False

    Example:
        user = query_db('SELECT * FROM users WHERE uId = ?', (uid,), one=True)
        if user:
            print(user['uname'])
    """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def init_db():
    """
    Initialize the database by executing schema.sql.

    Creates all tables (and the auto-release trigger) if they do not exist yet.
    Safe to call on every startup because schema.sql uses IF NOT EXISTS.

    Must be called inside an application context:
        with app.app_context():
            init_db()
    """
    db = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        db.executescript(f.read())
    db.commit()
