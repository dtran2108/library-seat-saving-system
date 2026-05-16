import os
from flask import Flask, render_template, session
from flask_wtf import CSRFProtect

from config import Config
from db import close_db, query_db, init_db
from routes.auth import auth_bp
from routes.seats import seats_bp
from routes.admin import admin_bp

_FRONTEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend')

app = Flask(
    __name__,
    template_folder=os.path.join(_FRONTEND, 'templates'),
    static_folder=os.path.join(_FRONTEND, 'static'),
)
app.config.from_object(Config)

csrf = CSRFProtect(app)
app.teardown_appcontext(close_db)

app.register_blueprint(auth_bp)
app.register_blueprint(seats_bp)
app.register_blueprint(admin_bp)


@app.context_processor
def inject_current_user():
    current_user = None
    if 'user_id' in session:
        current_user = query_db(
            'SELECT * FROM users WHERE uId = ?',
            (session['user_id'],),
            one=True
        )
    return dict(current_user=current_user)


@app.route('/')
def index():
    features = [
        {"icon": "map-pin",      "title": "Interactive Seat Map", "desc": "See the full floor plan with real-time availability at a glance."},
        {"icon": "clock",        "title": "Easy Booking",         "desc": "Reserve a seat for up to 4 hours. No more saving with bags!"},
        {"icon": "shield-check", "title": "Fair for Everyone",    "desc": "Confirmed reservations only — no phantom placeholders."},
        {"icon": "book-open",    "title": "Manage Your Sessions", "desc": "View, modify or cancel your upcoming bookings anytime."}
    ]
    return render_template("index.html", features=features)


with app.app_context():
init_db()

if __name__ == "__main__":
    app.run(debug=True)
