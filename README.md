# Library Seat Saving System

**NSYSU MIS205 — Group 6**

A web app where students log in with their student ID, browse a live floor-plan seat map, and reserve a seat at the library. Admins get a separate dashboard to manage zones, seats, and users.

**Tech used:** Python · Flask · SQLite · Jinja2 · Tailwind CSS v4

---

## Understanding this project's structure

Most web projects have two distinct sides. This project follows that same split:

```
library-seat-saving-system/
├── backend/    ← The Python server. Handles data, login, and page logic.
└── frontend/   ← The visual layer. HTML templates and CSS styling.
```

**Backend** (`backend/`) is Python. It runs on your computer as a server, talks to the database, checks whether you're logged in, and sends the right HTML page back to the browser.

**Frontend** (`frontend/`) is HTML + CSS. It defines what each page *looks* like — the layout, buttons, colours, and forms. In this project, Flask reads these HTML files and fills in the live data before sending them to the browser. The CSS is built by Tailwind, a Node.js tool.

> **Note:** This is not a traditional split where the frontend and backend are two separate running programs. Here the backend *uses* the frontend files — it just helps to keep them in separate folders so UI changes and server logic changes stay organised.

---

## Before you start

You need three tools installed on your computer. Run each "Check with" command in your terminal to see if you already have it.

| Tool | Required version | Check with |
|------|-----------------|------------|
| Python | 3.10 or newer | `python3 --version` |
| Node.js | 18 or newer | `node --version` |
| npm | comes with Node | `npm --version` |

If a command is not found, download the tool from its official website and re-check.

---

## First-time setup

Do these steps once after cloning the repo. After that, jump to [Daily development](#daily-development).

### Step 1 — Get the code

```bash
git clone https://github.com/dtran2108/library-seat-saving-system.git
cd library-seat-saving-system
```

### Step 2 — Create a Python virtual environment

```bash
# Create the environment (you only do this once)
python3 -m venv myenv

# Activate it — you must do this every time you open a new terminal
source myenv/bin/activate      # macOS and Linux
myenv\Scripts\activate         # Windows
```

### Step 3 — Install Python packages (backend)

Move into the `backend` folder and install the Python dependencies listed in `requirements.txt`:

```bash
cd backend
pip install -r requirements.txt
```

### Step 4 — Install Node packages (frontend)

Open a **second terminal**, move into `frontend`, and install the Node packages:

```bash
cd frontend
npm install
```

### Step 5 — Build the CSS

Still inside `frontend/`, run this to compile the Tailwind CSS:

```bash
npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css
```

You should see a new file appear at `frontend/static/css/output.css`. This file is what the browser actually loads. Never edit it by hand — it gets overwritten every time you rebuild.

### Step 6 — Create your environment file

Still in `backend/`, copy the example file:

```bash
cp .env.example .env
```

Now open `backend/.env` and replace the placeholder with a real secret key. You can generate one with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and paste it as the value of `SECRET_KEY` in `.env`. For local development this step is optional — the app has a fallback key built in — but get in the habit of doing it.

### Step 7 — Start the server

From `backend/`:

```bash
flask --app main run --debug
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser. If you see the landing page, everything is working.

---

## Daily development

Every time you sit down to work, you need two terminals running at the same time:

**Terminal 1 — CSS watcher** (from `frontend/`)
```bash
source ../myenv/bin/activate
cd frontend
npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css --watch
```
Leave this running. It automatically rebuilds the CSS whenever you edit a template.

**Terminal 2 — Flask server** (from `backend/`)
```bash
source ../myenv/bin/activate
cd backend
flask --app main run --debug
```
Leave this running too. The `--debug` flag auto-restarts the server whenever you save a Python file.

---

## Database guide

### How the database is created

The database file (`backend/library.db`) is created automatically on the first server start. You do not need to create it yourself. Flask runs `init_db()` at startup, which executes `backend/schema.sql` to create the tables.

`schema.sql` uses `CREATE TABLE IF NOT EXISTS` everywhere, so it is safe to run every startup — it skips tables that already exist.

### Starter data

`schema.sql` also pre-loads four zones (Learning Plaza A/B, Computer Area, Quiet Study Room) and 26 seats. This data is inserted with `INSERT OR IGNORE`, so it only runs once — re-starting the server will not duplicate it.

### Creating an admin account

The Sign Up page only creates student accounts. To create an admin, run this one-liner from `backend/` (replace the values in quotes):

```bash
python3 -c "
from werkzeug.security import generate_password_hash
from db import get_db
from main import app

with app.app_context():
    db = get_db()
    db.execute(
        'INSERT INTO users (uId, uname, password, role, ustatus) VALUES (?, ?, ?, ?, ?)',
        ('ADMIN001', 'Admin User', generate_password_hash('yourpassword'), 'admin', 'active')
    )
    db.commit()
    print('Done.')
"
```

### Resetting the database

Delete the database file and restart the server. It will be recreated from `schema.sql` with fresh starter data.

```bash
rm backend/library.db
cd backend && flask --app main run --debug
```

---

## Files at a glance

```
library-seat-saving-system/
│
├── README.md              ← You are here
├── .gitignore
│
├── backend/               ← Everything the Python server needs
│   ├── main.py            ← Page routes, login logic, app startup
│   ├── db.py              ← All database read/write helpers
│   ├── config.py          ← App settings (secret key, DB path)
│   ├── schema.sql         ← Defines database tables + starter data
│   ├── requirements.txt   ← Python packages this project needs
│   ├── .env.example       ← Copy this to .env and fill in your secret key
│   └── forms/
│       ├── __init__.py    ← Makes forms/ a Python package
│       └── auth.py        ← Login and sign-up form definitions
│
└── frontend/              ← Everything the browser sees
    ├── package.json       ← Node packages (just Tailwind CLI)
    ├── templates/         ← HTML pages (Flask fills these in with data)
    │   ├── layout.html            ← Shared HTML wrapper for public pages
    │   ├── dashboard-layout.html  ← Shared HTML wrapper for logged-in pages
    │   ├── index.html             ← Landing page
    │   ├── auth/
    │   │   ├── login.html
    │   │   └── sign-up.html
    │   ├── dashboard/
    │   │   ├── user-dashboard.html
    │   │   ├── admin-dashboard.html
    │   │   ├── seat-map.html
    │   │   ├── my-bookings.html
    │   │   └── manage-users.html
    │   └── components/    ← Reusable HTML snippets (Button, Input, Toast…)
    └── static/
        └── css/
            ├── input.css  ← Edit this file to change colours/fonts
            └── output.css ← Auto-generated — never edit this directly
```

---

## How it all works

You don't need to memorise all of this, but reading it once will save you a lot of confusion when something breaks.

---

### When you type a URL, what happens?

When your browser visits `http://127.0.0.1:5000/seat-map`, here is the sequence:

```
Browser                 Flask (backend/main.py)           Database
  |                           |                               |
  |--- GET /seat-map -------> |                               |
  |                           |--- SELECT zones, seats -----> |
  |                           |<-- rows of data ------------- |
  |                           |                               |
  |                    fills the HTML template
  |                    with the data
  |                           |
  |<-- finished HTML page --- |
```

In code, each URL is handled by a **route function** in `backend/main.py`:

```python
@app.route("/seat-map")    # "when someone visits /seat-map..."
@login_required            # "...first make sure they're logged in..."
def seat_map():
    zones = get_zones_with_seats()                    # fetch data
    return render_template("dashboard/seat-map.html", # fill template
                           zones=zones)               # pass data in
```

---

### How does the app know you're logged in?

When you log in successfully, Flask saves your student ID inside a **session cookie** — a small piece of data that lives in your browser. Every future request sends that cookie back to the server automatically, so Flask knows who you are.

```python
session['user_id'] = user['uId']   # save at login
session.clear()                    # wipe at logout
```

The cookie is **signed** with the `SECRET_KEY` from `config.py`, so its contents cannot be tampered with. But they can still be read, so we only store the student ID — never passwords or sensitive data.

---

### How is data read from and written to the database?

All database logic lives in `backend/db.py`. For reading, use `query_db()`:

```python
# Get one row (returns None if not found)
user = query_db('SELECT * FROM users WHERE uId = ?', (student_id,), one=True)

# Get all rows
zones = query_db('SELECT * FROM zones')
```

The `?` placeholder is important — it prevents SQL injection by keeping your data separate from the SQL command itself. Never build SQL by joining strings.

For creating or updating data, use `get_db()` directly and call `.commit()` to save:

```python
db = get_db()
db.execute('INSERT INTO users (...) VALUES (?)', (value,))
db.commit()   # without this, the change is not saved
```

---

### How do page templates work?

All HTML lives in `frontend/templates/`. Each page is a template file that gets filled in with real data by Flask before being sent to the browser. Think of a template like a form letter with blank fields — Flask fills in the blanks.

Every page shares a common shell via **template inheritance**. Instead of copying the header/footer/nav into every file, child templates just say "extend this parent" and fill in the unique part:

```html
{% extends "dashboard-layout.html" %}
{% block content %}
  <h1>This is the unique content of this page.</h1>
{% endblock %}
```

`dashboard-layout.html` defines the sidebar, topbar, and all the shared HTML. Change it once and every dashboard page updates automatically.

---

### What are the files in `frontend/templates/components/`?

These are **macros** — reusable HTML snippets you call like functions. Instead of copy-pasting the same button HTML in ten places, you define it once and import it:

```html
{% from "components/ui/button.html" import Button %}
{{ Button("Save Changes", variant="outline") }}
```

If the button design needs to change, you change it in one place and every page is updated.

---

### How are forms protected?

Forms need two layers of protection:

1. **Browser validation** — the `required` attribute on an input field stops the form from being submitted if the field is empty. Quick, but easy to bypass (anyone can edit the HTML).

2. **Server validation** — `form.validate_on_submit()` in `main.py` re-checks everything in Python even if someone bypassed the browser. This is the real protection.

3. **CSRF token** — every form includes a hidden token generated by Flask. This stops a malicious website from tricking your browser into submitting a form on your behalf. The `{{ form.hidden_tag() }}` line in every template is what adds that token. Do not remove it.

---

### How are restricted pages protected?

Decorators in `backend/main.py` guard pages that only logged-in (or admin) users should see:

```python
@app.route("/seat-map")
@login_required         # turns away anyone not logged in
def seat_map():
    ...

@app.route("/admin-dashboard")
@admin_required         # turns away anyone who isn't an admin
def admin_dashboard():
    ...
```

`@login_required` does three checks in order: is there a session cookie? → does that user ID still exist in the database? → is the account active? If any check fails, the user is sent back to the login page.

---

## Adding new features

### New page

1. Add a route function in `backend/main.py`:
   ```python
   @app.route("/my-page")
   @login_required
   def my_page():
       return render_template("dashboard/my-page.html")
   ```
2. Create `frontend/templates/dashboard/my-page.html` with `{% extends "dashboard-layout.html" %}`.
3. Add a link to the sidebar in `frontend/templates/dashboard-layout.html`.

### New form

1. Add a form class in `backend/forms/auth.py` (or a new file in `backend/forms/`).
2. Export it from `backend/forms/__init__.py`.
3. Import it in `backend/main.py`, create an instance, and pass it to `render_template`.
4. In the template, add `{{ form.hidden_tag() }}` as the first thing inside `<form>`.

### New database table

1. Add `CREATE TABLE IF NOT EXISTS ...` to `backend/schema.sql`.
2. Add any starter rows with `INSERT OR IGNORE`.
3. Delete `backend/library.db` and restart the server so the new table is created.
4. Read with `query_db()`, write with `get_db().execute()` + `.commit()`.

---

## Something not working?

| What you see | Why it happens | How to fix it |
|---|---|---|
| `RuntimeError: No application found` | You ran a Python file outside Flask's context | Run via `flask --app main run` from `backend/`, or wrap the code in `with app.app_context():` |
| `400 Bad Request` on a form | The CSRF token is missing | Make sure `{{ form.hidden_tag() }}` is the first line inside your `<form>` tag |
| Page looks unstyled / CSS missing | The Tailwind output file wasn't built | Run the build command from `frontend/`, or start watch mode |
| Old schema after adding a table | The database file predates your change | Delete `backend/library.db` and restart the server |
| `OperationalError: no such table` | The database was not initialized | Make sure the server starts without errors; `init_db()` runs at startup |
| Login redirects to itself forever | You're already logged in | Clear browser cookies, or open an incognito window |
