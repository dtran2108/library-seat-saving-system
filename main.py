from flask import Flask, render_template
import secrets

from forms import LoginForm, SignUpForm
from flask_wtf import CSRFProtect

app = Flask(__name__)

# secret key prevents malicious hijacking of form from an outside submission
secret = secrets.token_urlsafe(16)
app.secret_key = secret

# forms in Flask
csrf = CSRFProtect(app)

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

 
if __name__ == "__main__":
    app.run(debug=True)