# Library Seat Saving System

**NSYSU MIS205 — Group 6**  
A web application for reserving library seats at NSYSU. Students log in with their student ID, browse an interactive floor-plan seat map, and book a seat for a time slot. Admins manage zones, seats, and users from a separate dashboard.

**Stack:** Python · Flask · SQLite · Jinja2 · Tailwind CSS v4

---

## Getting Started

Follow these steps in order. Every command runs from the project root (the folder that contains `main.py`).

### 1. Prerequisites

| Tool | Version | Check with |
|------|---------|------------|
| Python | 3.10 or newer | `python3 --version` |
| Node.js | 18 or newer | `node --version` |
| npm | bundled with Node | `npm --version` |

### 2. Clone the repository

```bash
git clone https://github.com/dtran2108/library-seat-saving-system.git
cd library-seat-saving-system
```

### 3. Create and activate a virtual environment

A virtual environment keeps project dependencies isolated from the rest of your system.

```bash
# Create the environment (only needed once)
python3 -m venv myenv

# Activate it — you must do this every time you open a new terminal
source myenv/bin/activate        # macOS / Linux
myenv\Scripts\activate           # Windows
```

Your prompt will show `(myenv)` when the environment is active.

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Install Node dependencies (for Tailwind CSS)

```bash
npm install
```

### 6. Build the CSS

Tailwind scans the templates and generates a single optimised CSS file.

```bash
# One-time build
npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css

# Watch mode — rebuilds automatically whenever you edit a template
npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css --watch
```

### 7. Configure your environment

```bash
# Copy the example file
cp .env.example .env
```

Open `.env` and replace the placeholder with a real secret key:

```bash
# Generate a strong key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Paste the output as the value of `SECRET_KEY` in `.env`. For local development the fallback key in `config.py` works fine, but **never use it in production**.

### 8. Run the development server

```bash
flask --app main run --debug
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## Configuring the Database

### How it is created

The database (`library.db`) is created automatically the first time you start the server. Flask calls `init_db()` inside `main.py`:

```python
with app.app_context():
    init_db()
```

`init_db()` runs `schema.sql`, which uses `CREATE TABLE IF NOT EXISTS` everywhere, so it is safe to call on every startup — it will not overwrite existing data.

### Seed data

`schema.sql` also contains `INSERT OR IGNORE` statements that pre-populate four zones and 26 seats. These only insert when a row with that primary key does not already exist, so they are idempotent (running them twice is the same as running them once).

### Creating an admin account

New accounts created through the Sign Up page always have `role = 'user'`. To create an admin, open a Python shell inside the project:

```bash
python3 -c "
from werkzeug.security import generate_password_hash
from db import get_db, init_db
from main import app

with app.app_context():
    db = get_db()
    db.execute(
        'INSERT INTO users (uId, uname, password, role, ustatus) VALUES (?, ?, ?, ?, ?)',
        ('ADMIN001', 'Admin User', generate_password_hash('yourpassword'), 'admin', 'active')
    )
    db.commit()
    print('Admin created.')
"
```

### Resetting the database

Delete `library.db` and restart the server. The file will be re-created from `schema.sql` with fresh seed data.

```bash
rm library.db
flask --app main run --debug
```

---

## Project Structure

```
library-seat-saving-system/
│
├── main.py            ← Flask app: routes, auth decorators, app setup
├── db.py              ← Database helpers (get_db, query_db, init_db, get_zones_with_seats)
├── config.py          ← Flask Config class (SECRET_KEY, DATABASE path)
├── forms/             ← WTForms form classes
│   ├── __init__.py
│   └── auth.py        ← LoginForm, SignUpForm
├── schema.sql         ← Database schema + seed data (source of truth for the DB)
├── requirements.txt   ← Python dependencies
├── package.json       ← Node dependencies (Tailwind CLI)
│
├── static/
│   └── css/
│       ├── input.css  ← Tailwind entry point (edit this, not output.css)
│       └── output.css ← GENERATED — do not edit by hand; re-run the build command
│
└── templates/
    ├── layout.html            ← Base HTML for public pages (login, sign-up, index)
    ├── dashboard-layout.html  ← Base HTML for all dashboard pages (sidebar + topbar)
    ├── index.html
    ├── auth/
    │   ├── login.html
    │   └── sign-up.html
    ├── dashboard/
    │   ├── user-dashboard.html
    │   ├── admin-dashboard.html
    │   ├── seat-map.html
    │   ├── my-bookings.html
    │   └── manage-users.html
    └── components/            ← Reusable Jinja2 macros (Button, Input, Toast, etc.)
```

---

## Must-Know Concepts

This section explains *why* the code is structured the way it is. Understanding these patterns will help you add features without breaking anything.

---

### 1. The Flask Request–Response Cycle

Every time a browser makes a request (e.g. `GET /seat-map`), Flask:

1. Matches the URL to a **route function** (decorated with `@app.route`).
2. Runs that function.
3. The function calls `render_template(...)`, which fills a Jinja2 HTML template with data.
4. Flask sends the resulting HTML back to the browser as a **response**.

```python
@app.route("/seat-map")
@login_required
def seat_map():
    zones = get_zones_with_seats()                          # 1. fetch data from DB
    return render_template("dashboard/seat-map.html",       # 2. render template
                           zones=zones)                     # 3. pass data to template
```

To add a new page: add a route in `main.py`, create a template in `templates/`, link to it.

---

### 2. The Database Pattern (`db.py` and Flask `g`)

We use Python's built-in `sqlite3` module — no ORM. The pattern has three parts:

**`get_db()`** — opens a connection and caches it in `flask.g`:

```python
def get_db():
    if 'db' not in g:               # only open once per request
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row   # makes rows dict-like: row['uname']
    return g.db
```

`flask.g` is a **per-request scratch space** that Flask clears after every response. Think of it as a temporary shelf that exists only for the duration of one request.

**`close_db()`** — registered as a teardown handler so Flask closes the connection automatically:

```python
app.teardown_appcontext(close_db)   # main.py
```

**`query_db()`** — a thin wrapper around `cursor.execute` for SELECT queries:

```python
# one=True → return a single row (or None)
user = query_db('SELECT * FROM users WHERE uId = ?', (uid,), one=True)
print(user['uname'])

# one=False (default) → return a list
all_zones = query_db('SELECT * FROM zones')
```

For INSERT/UPDATE/DELETE, use `get_db()` directly and call `db.commit()`:

```python
db = get_db()
db.execute('INSERT INTO users (...) VALUES (?)', (value,))
db.commit()
```

---

### 3. WTForms and CSRF Protection

We use **Flask-WTF** to define form fields and validators in Python (in `forms/auth.py`), then render them in Jinja2 templates. This gives us two things for free:

- **Validation** — `form.validate_on_submit()` checks all validators (DataRequired, Length, EqualTo, etc.) and returns `False` if anything fails, so the form re-renders with error messages.
- **CSRF tokens** — `csrf = CSRFProtect(app)` in `main.py` and `{{ form.hidden_tag() }}` in every template together prevent cross-site request forgery attacks. Never remove `hidden_tag()` from a form.

```python
# forms/auth.py
class LoginForm(FlaskForm):
    student_id = StringField('Student ID', validators=[DataRequired()])
    password   = PasswordField('Password',  validators=[DataRequired()])
    submit     = SubmitField('Login')
```

```python
# main.py route
if login_form.validate_on_submit():   # True only on POST with valid data + valid CSRF
    student_id = login_form.student_id.data
    ...
```

---

### 4. Route Protection Decorators

Two custom decorators in `main.py` guard protected pages:

```python
@app.route("/seat-map")
@login_required        # ← blocks unauthenticated users
def seat_map():
    ...

@app.route("/admin-dashboard")
@admin_required        # ← blocks non-admin users (implies login check too)
def admin_dashboard():
    ...
```

`login_required` performs three checks in order:
1. Is `user_id` in the session? (Did this browser log in?)
2. Does that `user_id` exist in the `users` table? (Handles DB resets / deleted accounts.)
3. Is the account not suspended?

If any check fails, the session is cleared and the user is redirected to `/login`.

---

### 5. Jinja2 Template Inheritance

All pages share a common HTML shell via **template inheritance**.

Public pages (`login.html`, `sign-up.html`) extend `layout.html`:

```jinja2
{% extends "layout.html" %}
{% block content %}
  <p>Page-specific content goes here.</p>
{% endblock %}
```

Dashboard pages extend `dashboard-layout.html` (adds sidebar and topbar):

```jinja2
{% extends "dashboard-layout.html" %}
{% block content %}
  ...
{% endblock %}
```

`layout.html` and `dashboard-layout.html` define `{% block content %}{% endblock %}` as a placeholder. Child templates fill that placeholder with their own HTML. Every other part of the page (head, nav, footer, toast container) lives only in the parent — one change there updates every page.

---

### 6. Reusable Macros (`templates/components/`)

Macros are Jinja2's equivalent of functions or components. They avoid copy-pasting the same HTML in many places.

```jinja2
{# Import the macro at the top of your template #}
{% from "components/ui/button.html" import Button %}

{# Call it like a function #}
{{ Button("Save Changes", variant="outline") }}
```

To add a new component, create a file in `templates/components/`, define a `{% macro %}`, and import it wherever you need it.

---

### 7. Sessions (How Login State Is Stored)

Flask's `session` is a **signed cookie** stored in the browser. We put `user_id` into it at login and clear it at logout:

```python
session['user_id'] = user['uId']   # login
session.clear()                    # logout
```

Because the cookie is **signed** (not encrypted), the server can detect tampering — but the contents are still readable by anyone with the cookie. Never store sensitive data (passwords, tokens) in the session.

---

## Development Workflow

### Adding a new page

1. Add a route in `main.py`:
   ```python
   @app.route("/my-new-page")
   @login_required
   def my_new_page():
       return render_template("dashboard/my-new-page.html")
   ```
2. Create `templates/dashboard/my-new-page.html` extending `dashboard-layout.html`.
3. Add a link to it in `templates/dashboard-layout.html` (the sidebar `nav_items` list).

### Adding a new form

1. Define the form class in `forms/auth.py` (or a new file under `forms/`).
2. Export it from `forms/__init__.py`.
3. Import it in `main.py` and pass an instance to `render_template`.
4. In the template, call `{{ form.hidden_tag() }}` inside `<form>` and render each field.

### Adding a new database table

1. Add the `CREATE TABLE IF NOT EXISTS` statement to `schema.sql`.
2. Add any seed rows using `INSERT OR IGNORE`.
3. Reset the database (`rm library.db`) and restart the server.
4. Use `query_db()` for SELECT and `get_db().execute()` + `.commit()` for writes.

---

## Common Issues

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `RuntimeError: No application found` | Running code outside an app context | Use `with app.app_context():` or run via `flask --app main run` |
| `400 Bad Request` on form submit | Missing `{{ form.hidden_tag() }}` in template | Add it as the first line inside `<form>` |
| CSS changes not showing | Tailwind output not rebuilt | Re-run the build command or start watch mode |
| Old data showing after schema change | DB not reset | `rm library.db` then restart |
| `OperationalError: no such table` | DB not initialised | Ensure `init_db()` is called in `main.py` and restart |
