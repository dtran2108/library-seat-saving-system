from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session
from decorators import login_required
from controllers.seats import (
    get_zones_with_seats,
    update_expired_reservations,
    get_available_seats,
    book_seat,
    get_user_reservations,
    cancel_reservation,
    check_in_reservation,
    CHECK_IN_GRACE_MINUTES,
)

seats_bp = Blueprint('seats', __name__)

DB_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
ACTIVE_STATUSES = ('upcoming', 'active')
HISTORY_STATUSES = ('completed', 'cancelled', 'no_show')


def _decorate_reservation(row):
    start = datetime.strptime(row['startTime'], DB_DATETIME_FORMAT)
    end = datetime.strptime(row['endTime'], DB_DATETIME_FORMAT)
    row['booking_date'] = start.strftime('%A, %B %d, %Y')
    row['start_time'] = start.strftime('%H:%M')
    row['end_time'] = end.strftime('%H:%M')
    row['seat_label'] = f"{row['zoneName']} · {row['deskNo']}"

    deadline = start + timedelta(minutes=CHECK_IN_GRACE_MINUTES)
    row['check_in_deadline'] = deadline.strftime('%H:%M')
    row['checked_in'] = row.get('checkInId') is not None
    row['can_check_in'] = (
        row['status'] == 'active'
        and not row['checked_in']
        and datetime.now() <= deadline
    )
    return row


@seats_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def user_dashboard():
    reservations = [_decorate_reservation(r) for r in get_user_reservations(session['user_id'])]
    upcoming = [r for r in reservations if r['status'] in ACTIVE_STATUSES]
    upcoming.sort(key=lambda r: r['startTime'])
    return render_template("dashboard/user-dashboard.html", upcoming_bookings=upcoming)


@seats_bp.route('/seat-map')
@login_required
def seat_map():
    update_expired_reservations()
    zones = get_zones_with_seats()
    return render_template("dashboard/seat-map.html", zones=zones, today=date.today().isoformat())


@seats_bp.route('/my-bookings')
@login_required
def my_bookings():
    reservations = [_decorate_reservation(r) for r in get_user_reservations(session['user_id'])]
    upcoming = [r for r in reservations if r['status'] in ACTIVE_STATUSES]
    history = [r for r in reservations if r['status'] in HISTORY_STATUSES]
    return render_template(
        "dashboard/my-bookings.html",
        upcoming_bookings=upcoming,
        history_bookings=history,
    )


@seats_bp.route('/api/book', methods=['POST'])
@login_required
def api_book():
    seat_id      = request.form.get('seat_id', '').strip()
    booking_date = request.form.get('booking_date', '').strip()
    start_time   = request.form.get('start_time', '').strip()
    duration     = request.form.get('duration', '').strip()

    success, message = book_seat(session['user_id'], seat_id, booking_date, start_time, duration)
    if success:
        return jsonify(success=True, message=message)
    return jsonify(success=False, error=message), 400


@seats_bp.route('/api/available')
@login_required
def api_available():
    booking_date = request.args.get('booking_date', '').strip()
    start_time = request.args.get('start_time', '').strip()
    duration = request.args.get('duration', '').strip()
    zone_id = request.args.get('zone_id', '').strip() or None

    success, result = get_available_seats(
        booking_date,
        start_time,
        duration,
        zone_id
    )

    if success:
        return jsonify(success=True, seats=result)

    return jsonify(success=False, error=result), 400


@seats_bp.route('/api/my-bookings')
@login_required
def api_my_bookings():
    reservations = get_user_reservations(session['user_id'])
    return jsonify(success=True, reservations=reservations)


@seats_bp.route('/api/cancel/<int:reservation_id>', methods=['POST', 'DELETE'])
@login_required
def api_cancel(reservation_id):
    success, message = cancel_reservation(
        reservation_id,
        session['user_id'],
        session.get('role') == 'admin'
    )

    if success:
        return jsonify(success=True, message=message)

    return jsonify(success=False, error=message), 400


@seats_bp.route('/api/check-in/<int:reservation_id>', methods=['POST'])
@login_required
def api_check_in(reservation_id):
    success, message = check_in_reservation(reservation_id, session['user_id'])
    if success:
        return jsonify(success=True, message=message)
    return jsonify(success=False, error=message), 400
