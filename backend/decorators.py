from functools import wraps
from flask import session, flash, redirect, url_for
from db import query_db


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        user = query_db(
            'SELECT uId, ustatus FROM users WHERE uId = ?',
            (session['user_id'],),
            one=True
        )
        if not user:
            session.clear()
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))

        if user['ustatus'] == 'suspended':
            session.clear()
            flash('Your account has been suspended. Please contact the library staff.', 'error')
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        user = query_db('SELECT * FROM users WHERE uId = ?', (session['user_id'],), one=True)
        if not user or user['role'] != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('seats.user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function
