"""
main.py — entry point for the Library Seat Saving System.

Handles:
    - User authentication (login, sign-up, logout)
    - Route protection via @login_required decorator
    - current_user injection into all templates
    - Page routing for dashboard, seat map, bookings, admin pages
"""

import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from forms import LoginForm, SignUpForm
from flask_wtf import CSRFProtect
from db import get_db, close_db, query_db, init_db

app = Flask(__name__)

# Secret key for session cookies and CSRF protection.
# Set SECRET_KEY in your environment for production; the fallback is dev-only.
app.secret_key = os.environ.get('SECRET_KEY', 'nsysu-library-dev-key-change-in-production')

# CSRF protection for all forms
csrf = CSRFProtect(app)

# Register database teardown — auto-closes the SQLite connection after each request
app.teardown_appcontext(close_db)


# ──────────────────────────────────────────────
# Auth Helpers
# ──────────────────────────────────────────────

def login_required(f):
    """
    Decorator to protect routes that require authentication.

    Three checks in order:
      1. Session must contain 'user_id' (i.e. the user went through login).
      2. The user_id must resolve to a real row in the database — guards
         against stale cookies left over after a DB reset or user deletion.
      3. The account must not be suspended.

    Any failure clears the session and redirects to the login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))

        user = query_db(
            'SELECT uId, ustatus FROM users WHERE uId = ?',
            (session['user_id'],),
            one=True
        )
        if not user:
            # Stale session — the user no longer exists in the database.
            session.clear()
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('login'))

        if user['ustatus'] == 'suspended':
            session.clear()
            flash('Your account has been suspended. Please contact the library staff.', 'error')
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator to protect routes that require admin privileges.
    
    Checks that the user is logged in AND has role='admin'.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = query_db('SELECT * FROM users WHERE uId = ?', (session['user_id'],), one=True)
        if not user or user['role'] != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_current_user():
    """
    Make `current_user` available in all Jinja templates.
    
    If the user is logged in (session has 'user_id'), fetch their data
    from the database. Otherwise, current_user is None.
    
    Template usage:
        {% if current_user %}
            Hello, {{ current_user.uname }}!
        {% endif %}
    """
    current_user = None
    if 'user_id' in session:
        current_user = query_db(
            'SELECT * FROM users WHERE uId = ?',
            (session['user_id'],),
            one=True
        )
    return dict(current_user=current_user)


# ──────────────────────────────────────────────
# Database Initialization
# ──────────────────────────────────────────────

with app.app_context():
    init_db()


# ──────────────────────────────────────────────
# Public Routes
# ──────────────────────────────────────────────

@app.route("/")
def index():
    """Landing page — shows features and CTA buttons."""
    features = [
        {"icon": "map-pin", "title": "Interactive Seat Map", "desc": "See the full floor plan with real-time availability at a glance."},
        {"icon": "clock", "title": "Easy Booking", "desc": "Reserve a seat for up to 4 hours. No more saving with bags!"},
        {"icon": "shield-check", "title": "Fair for Everyone", "desc": "Confirmed reservations only — no phantom placeholders."},
        {"icon": "book-open", "title": "Manage Your Sessions", "desc": "View, modify or cancel your upcoming bookings anytime."}
    ]
    return render_template("index.html", features=features)


@app.route("/login", methods=['GET', 'POST'])
def login():
    """
    Login page — authenticates students by Student ID and password.
    
    GET:  Render login form
    POST: Validate credentials → set session → redirect to dashboard
    """
    # If already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('user_dashboard'))

    login_form = LoginForm()
    message = ""

    if login_form.validate_on_submit():
        student_id = login_form.student_id.data
        password = login_form.password.data

        # Look up the user by Student ID (uId in ER model)
        user = query_db(
            'SELECT * FROM users WHERE uId = ?',
            (student_id,),
            one=True
        )

        if user and check_password_hash(user['password'], password):
            # Check if the account is suspended
            if user['ustatus'] == 'suspended':
                message = "Your account has been suspended. Please contact the library staff."
            else:
                # Successful login — store user ID in session
                session['user_id'] = user['uId']
                flash(f'Welcome back, {user["uname"]}!', 'success')

                # Redirect admin to admin dashboard, students to user dashboard
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('user_dashboard'))
        else:
            message = "Invalid Student ID or password."

    return render_template("auth/login.html", form=login_form, message=message)


@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    """
    Sign-up page — creates a new student account.
    
    GET:  Render sign-up form
    POST: Validate form → hash password → INSERT into users → redirect to login
    
    Note: Only students can sign up. Admins are created manually in the database.
    """
    # If already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('user_dashboard'))

    sign_up_form = SignUpForm()
    message = ""

    if sign_up_form.validate_on_submit():
        student_id = sign_up_form.student_id.data
        full_name = sign_up_form.full_name.data
        phone_no = sign_up_form.phone_no.data or ''
        password = sign_up_form.password.data

        # Check if a user with this Student ID already exists
        existing_user = query_db(
            'SELECT uId FROM users WHERE uId = ?',
            (student_id,),
            one=True
        )

        if existing_user:
            message = "An account with this Student ID already exists."
        else:
            # Hash the password before storing
            hashed_password = generate_password_hash(password)

            # Insert the new user into the database
            db = get_db()
            db.execute(
                'INSERT INTO users (uId, uname, phoneNo, password, role, ustatus) VALUES (?, ?, ?, ?, ?, ?)',
                (student_id, full_name, phone_no, hashed_password, 'user', 'active')
            )
            db.commit()

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template("auth/sign-up.html", form=sign_up_form, message=message)


@app.route("/logout")
def logout():
    """Log out the current user by clearing the session."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ──────────────────────────────────────────────
# Protected Routes — Students
# ──────────────────────────────────────────────

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def user_dashboard():
    """Student dashboard — shows welcome message, quick actions, upcoming bookings."""
    return render_template("dashboard/user-dashboard.html")


def _get_zones_with_seats():
    """
    Build a list of zone dicts, each containing its seats.

    Returns a list of dicts with keys:
        zoneId, name, location, zone_status,
        seats       — list of seat dicts (seatId, destNo, status)
        total       — total seat count in the zone
        available   — count of seats with status='available'

    Used by both seat_map and admin_dashboard so the query lives here once.
    """
    zones = query_db('SELECT * FROM zones ORDER BY zoneId')
    result = []
    for zone in zones:
        seats = query_db(
            'SELECT seatId, destNo, status FROM seats WHERE zoneId = ? ORDER BY destNo',
            (zone['zoneId'],)
        )
        seat_list = [dict(s) for s in seats]
        result.append({
            'zoneId':      zone['zoneId'],
            'name':        zone['name'],
            'location':    zone['location'],
            'zone_status': zone['status'],
            'seats':       seat_list,
            'total':       len(seat_list),
            'available':   sum(1 for s in seat_list if s['status'] == 'available'),
        })
    return result


@app.route("/seat-map")
@login_required
def seat_map():
    """Seat map page — interactive floor plan for booking seats."""
    zones = _get_zones_with_seats()
    return render_template("dashboard/seat-map.html", zones=zones)


@app.route("/my-bookings")
@login_required
def my_bookings():
    """My Bookings page — view, cancel upcoming and past bookings."""
    return render_template("dashboard/my-bookings.html")


# ──────────────────────────────────────────────
# Protected Routes — Admin
# ──────────────────────────────────────────────

@app.route("/admin-dashboard", methods=["GET", "POST"])
@admin_required
def admin_dashboard():
    """Admin dashboard — manage bookings and seats."""
    zones = _get_zones_with_seats()

    # Aggregate seat stats across all zones in one query.
    stats = query_db(
        '''SELECT COUNT(*) AS total,
                  SUM(CASE WHEN status = "maintenance" THEN 1 ELSE 0 END) AS blocked
           FROM seats''',
        one=True
    )
    total_seats  = stats['total']   or 0
    blocked_seats = stats['blocked'] or 0

    return render_template(
        "dashboard/admin-dashboard.html",
        zones=zones,
        total_seats=total_seats,
        blocked_seats=blocked_seats,
    )


@app.route("/manage-users")
@admin_required
def manage_users():
    """Admin user management page — view and update user roles."""
    return render_template("dashboard/manage-users.html")


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)