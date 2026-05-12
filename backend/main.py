# main.py — Flask application entry point.
#
# This file does four things:
#   1. Creates the Flask app and points it at the frontend/ folder.
#   2. Defines decorators that block pages from unauthenticated users.
#   3. Defines every URL route (what happens when a browser visits a path).
#   4. Starts the database on first run.

import os
from functools import wraps
from datetime import date, datetime, timedelta
from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from forms import LoginForm, SignUpForm
from flask_wtf import CSRFProtect
from db import get_db, close_db, query_db, init_db, get_zones_with_seats

# __file__ always refers to this Python file, so this path is correct no matter
# which directory you run "flask run" from.
_FRONTEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend')

app = Flask(
    __name__,
    template_folder=os.path.join(_FRONTEND, 'templates'),
    static_folder=os.path.join(_FRONTEND, 'static'),
)
app.config.from_object(Config)

# Without CSRF protection, a malicious website could submit one of our forms
# on behalf of a logged-in user without their knowledge.
csrf = CSRFProtect(app)

# Registering close_db here means Flask calls it automatically after every
# request — we never have to remember to close the database connection manually.
app.teardown_appcontext(close_db)


# ── Auth decorators ────────────────────────────────────────────────────────────
#
# A decorator wraps a route function with extra logic that runs first.
# Adding @login_required above a route is like putting a locked door in front
# of it — the user only gets in if all checks pass.

def login_required(f):
    @wraps(f)  # preserves the original function's name so Flask routing still works
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))

        # Checking the database here (not just the session cookie) prevents a
        # deleted or reset account from staying "logged in" via an old cookie.
        user = query_db(
            'SELECT uId, ustatus FROM users WHERE uId = ?',
            (session['user_id'],),
            one=True
        )
        if not user:
            session.clear()
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('login'))

        if user['ustatus'] == 'suspended':
            # Clear the session so the user can't retry by going back.
            session.clear()
            flash('Your account has been suspended. Please contact the library staff.', 'error')
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
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


# ── Template context ───────────────────────────────────────────────────────────

@app.context_processor
def inject_current_user():
    # Templates cannot call Python functions on their own, so we use a context
    # processor to push data into every template automatically. Any template can
    # now use {{ current_user }} without the route needing to pass it explicitly.
    current_user = None
    if 'user_id' in session:
        current_user = query_db(
            'SELECT * FROM users WHERE uId = ?',
            (session['user_id'],),
            one=True
        )
    return dict(current_user=current_user)


# ── Database initialisation ────────────────────────────────────────────────────

# app_context() is required here because init_db() calls get_db(), which reads
# from current_app — a proxy that only works inside a request or app context.
with app.app_context():
    init_db()


# ── Public routes (no login needed) ───────────────────────────────────────────

@app.route("/")
def index():
    features = [
        {"icon": "map-pin", "title": "Interactive Seat Map", "desc": "See the full floor plan with real-time availability at a glance."},
        {"icon": "clock", "title": "Easy Booking", "desc": "Reserve a seat for up to 4 hours. No more saving with bags!"},
        {"icon": "shield-check", "title": "Fair for Everyone", "desc": "Confirmed reservations only — no phantom placeholders."},
        {"icon": "book-open", "title": "Manage Your Sessions", "desc": "View, modify or cancel your upcoming bookings anytime."}
    ]
    return render_template("index.html", features=features)


@app.route("/login", methods=['GET', 'POST'])
def login():
    # Redirect logged-in users away so they can't see the login page again.
    if 'user_id' in session:
        return redirect(url_for('user_dashboard'))

    login_form = LoginForm()
    message = ""

    if login_form.validate_on_submit():
        student_id = login_form.student_id.data
        password = login_form.password.data

        user = query_db(
            'SELECT * FROM users WHERE uId = ?',
            (student_id,),
            one=True
        )

        if user and check_password_hash(user['password'], password):
            if user['ustatus'] == 'suspended':
                message = "Your account has been suspended. Please contact the library staff."
            else:
                # Storing only the ID (not the whole user object) keeps the
                # cookie small and avoids stale data on subsequent requests.
                session['user_id'] = user['uId']
                flash(f'Welcome back, {user["uname"]}!', 'success')

                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('user_dashboard'))
        else:
            # Use the same error message for both "wrong ID" and "wrong password"
            # so attackers can't tell which one they got right.
            message = "Invalid Student ID or password."

    return render_template("auth/login.html", form=login_form, message=message)


@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if 'user_id' in session:
        return redirect(url_for('user_dashboard'))

    sign_up_form = SignUpForm()
    message = ""

    if sign_up_form.validate_on_submit():
        student_id = sign_up_form.student_id.data
        full_name = sign_up_form.full_name.data
        phone_no = sign_up_form.phone_no.data or ''
        password = sign_up_form.password.data

        existing_user = query_db(
            'SELECT uId FROM users WHERE uId = ?',
            (student_id,),
            one=True
        )

        if existing_user:
            message = "An account with this Student ID already exists."
        else:
            # Passwords must never be stored as plain text. generate_password_hash
            # produces a one-way hash — even if the database is leaked, the original
            # password cannot be recovered from it.
            hashed_password = generate_password_hash(password)

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
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ── Protected routes — students ────────────────────────────────────────────────

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def user_dashboard():
    return render_template("dashboard/user-dashboard.html")


@app.route("/seat-map")
@login_required
def seat_map():
    zones = get_zones_with_seats()
    return render_template("dashboard/seat-map.html", zones=zones, today=date.today().isoformat())


@app.route("/my-bookings")
@login_required
def my_bookings():
    return render_template("dashboard/my-bookings.html")


# ── Protected routes — admin ───────────────────────────────────────────────────

@app.route("/admin-dashboard", methods=["GET", "POST"])
@admin_required
def admin_dashboard():
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

    return render_template(
        "dashboard/admin-dashboard.html",
        zones=zones,
        total_seats=total_seats,
        blocked_seats=blocked_seats,
    )


@app.route("/api/book", methods=["POST"])
@login_required
def api_book():
    seat_id      = request.form.get('seat_id', '').strip()
    booking_date = request.form.get('booking_date', '').strip()
    start_time   = request.form.get('start_time', '').strip()
    duration     = request.form.get('duration', '').strip()

    if not all([seat_id, booking_date, start_time, duration]):
        return jsonify(success=False, error='All fields are required.')

    try:
        seat_id  = int(seat_id)
        duration = int(duration)
        if duration not in (1, 2, 3, 4):
            raise ValueError
    except ValueError:
        return jsonify(success=False, error='Invalid seat ID or duration.')

    try:
        start_dt = datetime.strptime(f'{booking_date} {start_time}', '%Y-%m-%d %H:%M')
    except ValueError:
        return jsonify(success=False, error='Invalid date or time format.')

    end_dt = start_dt + timedelta(hours=duration)

    seat = query_db('SELECT seatId, status FROM seats WHERE seatId = ?', (seat_id,), one=True)
    if not seat:
        return jsonify(success=False, error='Seat not found.')
    if seat['status'] != 'available':
        return jsonify(success=False, error='This seat is no longer available.')

    # Atomic update: only succeeds if no one else claimed the seat between the
    # check above and now. rowcount == 0 means another request won the race.
    db = get_db()
    cur = db.execute(
        "UPDATE seats SET status = 'booked' WHERE seatId = ? AND status = 'available'",
        (seat_id,)
    )
    if cur.rowcount == 0:
        return jsonify(success=False, error='This seat was just taken. Please choose another.')

    db.execute(
        'INSERT INTO reservations (uId, seatId, startTime, endTime, status) VALUES (?, ?, ?, ?, ?)',
        (
            session['user_id'],
            seat_id,
            start_dt.strftime('%Y-%m-%d %H:%M:%S'),
            end_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'active',
        )
    )
    db.commit()
    return jsonify(success=True, message='Seat booked successfully!')


@app.route("/manage-users")
@admin_required
def manage_users():
    return render_template("dashboard/manage-users.html")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
