"""
db.py — Database connection helpers for the Library Seat Saving System.

Uses Python's built-in sqlite3 module with parameterized queries.
Provides per-request connection management via Flask's `g` object.
"""

import sqlite3
from flask import g

# Path to the SQLite database file (created automatically if it doesn't exist)
DATABASE = 'library.db'


def get_db():
    """
    Get a database connection for the current request.
    
    The connection is stored in Flask's `g` object so it can be
    reused within the same request and automatically closed afterwards.
    Returns rows as sqlite3.Row objects (dict-like access by column name).
    """
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        # Return rows as sqlite3.Row so we can access columns by name
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    """
    Close the database connection at the end of a request.
    
    This function is registered as a teardown handler in main.py
    so it runs automatically after every request.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    """
    Execute a SQL query and return results as a list of Row objects.
    
    Args:
        query (str): The SQL query string with ? placeholders.
        args (tuple): Parameters to bind to the query (prevents SQL injection).
        one (bool): If True, return only the first row (or None).
    
    Returns:
        list[sqlite3.Row] or sqlite3.Row or None
    
    Example:
        user = query_db('SELECT * FROM users WHERE uId = ?', (student_id,), one=True)
        if user:
            print(user['uname'])
    """
    cur = get_db().execute(query, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def init_db():
    """
    Initialize the database by creating the users table if it doesn't exist.
    
    This is a minimal setup for authentication to work. The full schema
    (seats, reservations, penalties, etc.) will be provided later.
    
    Table mapping from ER model:
        uId      → Student ID (primary key, login identifier)
        uname    → Full name
        phoneNo  → Phone number
        password → Hashed password (via werkzeug.security)
        role     → 'user' or 'admin'
        ustatus  → 'active' or 'suspended'
    """
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            uId       TEXT PRIMARY KEY,
            uname     TEXT NOT NULL,
            phoneNo   TEXT DEFAULT '',
            password  TEXT NOT NULL,
            role      TEXT NOT NULL DEFAULT 'user',
            ustatus   TEXT NOT NULL DEFAULT 'active'
        )
    ''')
    db.commit()
