from flask import Flask, render_template
# TODO: Authentication
# from flask import request, redirect, url_for
# from flask_login import current_user
import secrets

from forms import LoginForm, SignUpForm
from flask_wtf import CSRFProtect

app = Flask(__name__)

# secret key prevents malicious hijacking of form from an outside submission
secret = secrets.token_urlsafe(16)
app.secret_key = secret

# forms in Flask
csrf = CSRFProtect(app)

# TODO: Authentication
# @app.before_request
# def check_student_id():
#     # If the user is logged in, doesn't have a student ID, 
#     # and isn't already on the setup page or logging out/serving static files
#     if current_user.is_authenticated and not current_user.student_id:
#         allowed_endpoints = ['profile_setup', 'logout', 'static']
#         if request.endpoint not in allowed_endpoints:
#             return redirect(url_for('profile_setup'))

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
    login_form = LoginForm()
    message = ""
    if login_form.validate_on_submit():
        message = "Invalid login credentials!"
    return render_template("auth/login.html", form=login_form, message=message)

@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    sign_up_form = SignUpForm()
    message = ""
    if sign_up_form.validate_on_submit():
        message = "Invalid login credentials!"
    return render_template("auth/sign-up.html", form=sign_up_form, message=message)

@app.route("/admin-dashboard", methods=["GET","POST"])
def admin_dashboard():
    return render_template("dashboard/admin-dashboard.html")

@app.route("/dashboard", methods=["GET","POST"])
def user_dashboard():
    return render_template("dashboard/user-dashboard.html")

@app.route("/seat-map")
def seat_map():
    return render_template("dashboard/seat-map.html")

@app.route("/my-bookings")
def my_bookings():
    return render_template("dashboard/my-bookings.html")

@app.route("/manage-users")
def manage_users():
    return render_template("dashboard/manage-users.html")
 
if __name__ == "__main__":
    app.run(debug=True)