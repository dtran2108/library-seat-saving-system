from flask import Blueprint, render_template, request, jsonify, session
from decorators import admin_required
from controllers.admin import get_dashboard_data, block_seat, unblock_seat

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin-dashboard', methods=['GET', 'POST'])
@admin_required
def admin_dashboard():
    zones, total_seats, blocked_seats = get_dashboard_data()
    return render_template(
        "dashboard/admin-dashboard.html",
        zones=zones,
        total_seats=total_seats,
        blocked_seats=blocked_seats,
    )


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
