from flask import Blueprint, render_template
from decorators import admin_required
from controllers.admin import get_dashboard_data

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
