# db.py — database helpers.
#
# All code that talks to SQLite lives here so the rest of the app never has to
# think about connections, cursors, or file paths.

import os
import sqlite3

from flask import current_app, g


def get_db():
    # Flask's `g` object is a per-request scratch space. By storing the
    # connection there, every part of the same request reuses one connection
    # instead of opening a new one for every query.
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        # Row objects let you access columns by name (row['uname']) instead of
        # by position (row[1]), which makes the code much easier to read.
        g.db.row_factory = sqlite3.Row
        # SQLite does not enforce foreign keys by default — this turns that on
        # so deleting a zone cannot leave orphan seats behind.
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(e=None):
    # g.pop returns None if no connection was opened (e.g. the request failed
    # before any DB call), so this is safe to call unconditionally.
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    # Using `?` placeholders instead of string formatting is what prevents
    # SQL injection — SQLite keeps the data and the SQL command separate.
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def init_db():
    db = get_db()
    # current_app.root_path is the directory where main.py lives (backend/),
    # so these paths are correct regardless of where you run flask from.
    # schema.sql must run first — seed.sql depends on the tables existing.
    for filename in ('schema.sql', 'seed.sql'):
        path = os.path.join(current_app.root_path, filename)
        with open(path) as f:
            db.executescript(f.read())

