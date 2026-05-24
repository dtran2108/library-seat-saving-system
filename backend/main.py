import os
from flask import Flask, render_template, session
from flask_wtf import CSRFProtect

from config import Config
from db import close_db, query_db, init_db
from routes.auth import auth_bp
from routes.seats import seats_bp
from routes.admin import admin_bp
from controllers.seats import get_zones_with_seats

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
    zones  = get_zones_with_seats()
    zone_a = next((z for z in zones if z['name'] == 'Learning Plaza A'), None)
    zone_b = next((z for z in zones if z['name'] == 'Learning Plaza B'), None)
    return render_template("index.html", zone_a=zone_a, zone_b=zone_b)


with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True)
