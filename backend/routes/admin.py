from datetime import date

from flask import Blueprint, render_template, request, jsonify, session, url_for
from decorators import admin_required
from controllers.admin import (
    get_dashboard_data,
    get_admin_kpis,
    get_hourly_bookings,
    get_metric_series,
    get_peak_hour_forecast,
    get_zone_summaries,
    recent_admin_actions,
    block_seat,
    unblock_seat,
    get_bookings_for_date,
    override_reservation,
    list_users,
    set_user_status,
    issue_user_penalty,
    revoke_user_penalty,
)
from controllers.seats import cancel_reservation
from controllers.system import is_booking_enabled, set_booking_enabled
from controllers.admin_invites import (
    create_invite,
    list_pending_invites,
    revoke_invite,
)

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
        booking_enabled=is_booking_enabled(),
        kpis=get_admin_kpis(),
        hourly_bookings=get_hourly_bookings(24),
        bookings_series=get_metric_series('bookings', 7),
        no_show_series=get_metric_series('no_shows', 7),
        peak_forecast=get_peak_hour_forecast(30),
        zone_summaries=get_zone_summaries(30, top_n=3),
        recent_actions=recent_admin_actions(8),
    )


@admin_bp.route('/api/admin/booking-system/toggle', methods=['POST'])
@admin_required
def api_admin_toggle_booking_system():
    enabled_param = request.form.get('enabled', '').strip().lower()
    if enabled_param not in ('true', 'false'):
        return jsonify(success=False, error='Invalid value for "enabled".'), 400
    success, message = set_booking_enabled(enabled_param == 'true', session['user_id'])
    return jsonify(success=success, message=message, enabled=enabled_param == 'true')


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


@admin_bp.route('/manage-seats')
@admin_required
def manage_seats():
    zones, total_seats, blocked_seats = get_dashboard_data()
    return render_template(
        "dashboard/manage-seats.html",
        zones=zones,
        total_seats=total_seats,
        blocked_seats=blocked_seats,
    )


@admin_bp.route('/manage-users')
@admin_required
def manage_users():
    return render_template(
        "dashboard/manage-users.html",
        users=list_users(),
        pending_invites=list_pending_invites(),
        current_admin_id=session['user_id'],
    )


@admin_bp.route('/api/admin/invites', methods=['POST'])
@admin_required
def api_admin_create_invite():
    uid   = request.form.get('uId', '').strip()
    uname = request.form.get('uname', '').strip()
    phone = request.form.get('phoneNo', '').strip()

    success, result = create_invite(uid, uname, phone, session['user_id'])
    if not success:
        return jsonify(success=False, error=result), 400

    signup_url = url_for('auth.admin_signup', token=result['token'], _external=True)
    return jsonify(success=True, invite={**result, 'signup_url': signup_url})


@admin_bp.route('/api/admin/invites/<int:invite_id>/revoke', methods=['POST'])
@admin_required
def api_admin_revoke_invite(invite_id):
    success, message = revoke_invite(invite_id, session['user_id'])
    if success:
        return jsonify(success=True, message=message)
    return jsonify(success=False, error=message), 400


@admin_bp.route('/api/admin/users')
@admin_required
def api_admin_users():
    return jsonify(success=True, users=list_users())


@admin_bp.route('/api/admin/users/<user_id>/suspend', methods=['POST'])
@admin_required
def api_admin_suspend_user(user_id):
    success, message = set_user_status(user_id, session['user_id'], 'suspended')
    if success:
        return jsonify(success=True, message=message)
    return jsonify(success=False, error=message), 400


@admin_bp.route('/api/admin/users/<user_id>/reactivate', methods=['POST'])
@admin_required
def api_admin_reactivate_user(user_id):
    success, message = set_user_status(user_id, session['user_id'], 'active')
    if success:
        return jsonify(success=True, message=message)
    return jsonify(success=False, error=message), 400


@admin_bp.route('/api/admin/users/<user_id>/penalty', methods=['POST'])
@admin_required
def api_admin_issue_penalty(user_id):
    reason   = request.form.get('reason', '').strip()
    end_date = request.form.get('end_date', '').strip()
    success, message = issue_user_penalty(user_id, session['user_id'], reason, end_date)
    if success:
        return jsonify(success=True, message=message)
    return jsonify(success=False, error=message), 400


@admin_bp.route('/api/admin/penalties/<int:penalty_id>/revoke', methods=['POST'])
@admin_required
def api_admin_revoke_penalty(penalty_id):
    success, message = revoke_user_penalty(penalty_id, session['user_id'])
    if success:
        return jsonify(success=True, message=message)
    return jsonify(success=False, error=message), 400


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
