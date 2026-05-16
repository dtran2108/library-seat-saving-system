from datetime import date
from flask import Blueprint, render_template, request, jsonify, session
from decorators import login_required
from controllers.seats import (
    get_seat_map_data,
    update_expired_reservations,
    get_available_seats,
    book_seat,
    get_user_reservations,
    cancel_reservation,
)

seats_bp = Blueprint('seats', __name__)


@seats_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def user_dashboard():
    return render_template("dashboard/user-dashboard.html")


@seats_bp.route('/seat-map')
@login_required
def seat_map():
    update_expired_reservations()
    zones = get_seat_map_data()
    return render_template("dashboard/seat-map.html", zones=zones, today=date.today().isoformat())


@seats_bp.route('/my-bookings')
@login_required
def my_bookings():
    return render_template("dashboard/my-bookings.html")



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


    return jsonify(success=False, error=message), 400
