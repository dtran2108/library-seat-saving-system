from datetime import date

from flask import Blueprint, render_template, request, jsonify, session
from decorators import admin_required
from controllers.admin import (
    get_dashboard_data,
    block_seat,
    unblock_seat,
    get_bookings_for_date,
    override_reservation,
)
from controllers.seats import cancel_reservation

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin-dashboard', methods=['GET', 'POST'])
@admin_required
def admin_dashboard():
    zones, total_seats, blocked_seats = get_dashboard_data()
    today = date.today().isoformat()
    _, bookings = get_bookings_for_date(today)
    return render_template(
        "dashboard/admin-dashboard.html",
        zones=zones,
        total_seats=total_seats,
        blocked_seats=blocked_seats,
        selected_date=today,
        bookings=bookings,
    )


@admin_bp.route('/api/admin/bookings')
@admin_required
def api_admin_bookings():
    booking_date = request.args.get('date', '').strip()
    success, result = get_bookings_for_date(booking_date)
    if success:
        return jsonify(success=True, bookings=result)
    return jsonify(success=False, error=result), 400


@admin_bp.route('/api/admin/override-reservation/<int:reservation_id>', methods=['POST'])
@admin_required
def api_admin_override_reservation(reservation_id):
    start_time = request.form.get('start_time', '').strip()
    duration   = request.form.get('duration', '').strip()

    success, message = override_reservation(
        reservation_id,
        session['user_id'],
        start_time,
        duration,
    )
    if success:
        return jsonify(success=True, message=message)
    return jsonify(success=False, error=message), 400


@admin_bp.route('/api/admin/cancel-reservation/<int:reservation_id>', methods=['POST'])
@admin_required
def api_admin_cancel_reservation(reservation_id):
    success, message = cancel_reservation(
        reservation_id,
        session['user_id'],
        is_admin=True,
    )
    if success:
        return jsonify(success=True, message=message)
    return jsonify(success=False, error=message), 400


@admin_bp.route('/manage-users')
@admin_required
def manage_users():
    return render_template("dashboard/manage-users.html")


@admin_bp.route('/api/admin/block-seat', methods=['POST'])
@admin_required
def api_block_seat():
    seat_id = request.form.get('seat_id', '').strip()
    success, message = block_seat(seat_id, session['user_id'])
    if success:
        return jsonify(success=True, message=message)
    return jsonify(success=False, error=message), 400


@admin_bp.route('/api/admin/unblock-seat', methods=['POST'])
@admin_required
def api_unblock_seat():
    seat_id = request.form.get('seat_id', '').strip()
    success, message = unblock_seat(seat_id, session['user_id'])
    if success:
        return jsonify(success=True, message=message)
    return jsonify(success=False, error=message), 400
