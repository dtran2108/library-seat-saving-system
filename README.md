# Library Seat Saving System

**NSYSU MIS205 — Group 6**

A web application where students log in with their student ID, browse a live floor-plan seat map, and reserve a library seat. Admins get a separate dashboard to manage zones, seats, and users.

**Tech stack:** Python · Flask · SQLite · Jinja2 · Tailwind CSS v4

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Development Guide](#3-development-guide)
   - [Prerequisites](#prerequisites)
   - [First-Time Setup — Backend](#first-time-setup--backend)
   - [First-Time Setup — Frontend](#first-time-setup--frontend)
   - [Daily Development](#daily-development)
4. [Database Guide](#4-database-guide)
5. [Must-Know Concepts](#5-must-know-concepts)
   - [The three-layer architecture](#the-three-layer-architecture)
   - [Why we split routes from controllers](#why-we-split-routes-from-controllers)
   - [How authentication and access control work](#how-authentication-and-access-control-work)
   - [How page templates work](#how-page-templates-work)
   - [How forms are protected](#how-forms-are-protected)
   - [How data is read from and written to the database](#how-data-is-read-from-and-written-to-the-database)
6. [Contributor Workflow](#6-contributor-workflow)
   - [The mental model: data → logic → delivery](#the-mental-model-data--logic--delivery)
   - [Backend workflow](#backend-workflow)
   - [Frontend workflow](#frontend-workflow)
   - [The one rule you must not break](#the-one-rule-you-must-not-break)
   - [Pre-PR checklist](#pre-pr-checklist)
7. [Adding New Features](#7-adding-new-features)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Project Overview

This system replaces the habit of saving library seats with bags. Students log in, pick a seat on a live floor plan, and get a confirmed reservation. Admins can see all zones, block seats for maintenance, and manage user accounts.

### The frontend / backend split

The project is split into two folders that each do a different job:

```
library-seat-saving-system/
├── backend/    ← Python server. Handles data, login, business logic, and page routing.
└── frontend/   ← Visual layer. HTML templates and compiled CSS styling.
```

**Backend** runs on your computer as a Python server. It reads and writes the database, checks whether you are logged in, applies booking rules, and hands the finished HTML page back to the browser.

**Frontend** defines what every page *looks like* — layout, buttons, colors, and forms. Flask reads these HTML files, fills in live data, and sends the result to the browser. The CSS is compiled by Tailwind, a Node.js tool.

> **Important:** This is not the classic "separate API + separate React app" split. The backend *serves* the frontend files — they are two folders inside one project, not two independently-running programs. You only ever start one server (`flask run`).

---

## 2. Repository Structure

```
library-seat-saving-system/
│
├── README.md                  ← You are here
├── ER-models.png              ← Entity-relationship diagram
│
├── backend/                   ← Everything the Python server needs
│   ├── main.py                ← App entry point: creates the Flask app, registers blueprints
│   ├── db.py                  ← Database connection and low-level query helpers
│   ├── decorators.py          ← @login_required and @admin_required guards
│   ├── config.py              ← App settings (secret key, database path)
│   ├── schema.sql             ← Defines all database tables and inserts starter data
│   ├── requirements.txt       ← Python packages this project needs
│   ├── .env.example           ← Copy to .env and fill in your secret key
│   │
│   ├── routes/                ← HTTP layer: one file per feature area
│   │   ├── auth.py            ← /login, /sign-up, /logout
│   │   ├── seats.py           ← /dashboard, /seat-map, /my-bookings, /api/book
│   │   └── admin.py           ← /admin-dashboard, /manage-users
│   │
│   ├── controllers/           ← Business logic layer: one file per feature area
│   │   ├── auth.py            ← authenticate_user(), register_user()
│   │   ├── seats.py           ← get_seat_map_data(), book_seat()
│   │   └── admin.py           ← get_dashboard_data()
│   │
│   └── forms/                 ← WTForms form definitions (field rules + validation)
│       └── auth.py            ← LoginForm, SignUpForm
│
└── frontend/                  ← Everything the browser sees
    ├── package.json           ← Node packages (Tailwind CLI)
    ├── templates/             ← HTML pages (Flask fills these in with live data)
    │   ├── layout.html                ← Shared shell for public pages
    │   ├── dashboard-layout.html      ← Shared shell for logged-in pages (sidebar, nav)
    │   ├── index.html                 ← Landing page
    │   ├── auth/
    │   │   ├── login.html
    │   │   └── sign-up.html
    │   ├── dashboard/
    │   │   ├── user-dashboard.html
    │   │   ├── admin-dashboard.html
    │   │   ├── seat-map.html
    │   │   ├── my-bookings.html
    │   │   └── manage-users.html
    │   └── components/                ← Reusable HTML snippets (Button, Input, Toast…)
    └── static/
        └── css/
            ├── input.css              ← Edit this to customize colors/fonts
            └── output.css             ← Auto-generated — never edit directly
```

---

## 3. Development Guide

### Prerequisites

You need three tools installed. Run the "Check with" command in your terminal to see if you already have each one.

| Tool | Required version | Check with |
|------|-----------------|------------|
| Python | 3.10 or newer | `python3 --version` |
| Node.js | 18 or newer | `node --version` |
| npm | comes with Node | `npm --version` |

If a command is not found, download the tool from its official website, install it, then check again.

---

### First-Time Setup — Backend

Do these steps once, right after cloning the repository.

**Step 1 — Get the code**

```bash
git clone https://github.com/dtran2108/library-seat-saving-system.git
cd library-seat-saving-system
```

**Step 2 — Create a Python virtual environment**

A virtual environment is a sandboxed Python installation just for this project. It keeps the packages you install here from conflicting with other projects on your computer.

```bash
# Run this once from the project root
python3 -m venv myenv
```

**Step 3 — Activate the virtual environment**

You must activate the environment every time you open a new terminal window.

```bash
# macOS / Linux
source myenv/bin/activate

# Windows (Command Prompt)
myenv\Scripts\activate
```

When it is active, your terminal prompt will show `(myenv)` at the start. If you don't see that prefix, the environment is not active — packages will not be found.

**Step 4 — Install Python packages**

```bash
cd backend
pip install -r requirements.txt
```

This reads `backend/requirements.txt` and installs Flask, Flask-WTF, WTForms, and Werkzeug.

**Step 5 — Create your environment file**

```bash
# Still inside backend/
cp .env.example .env
```

Open `backend/.env` and paste in a real secret key. Generate one with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the printed value and set it as `SECRET_KEY` in `.env`. For local development, the app has a fallback key so this step is optional — but get into the habit.

**Step 6 — Start the Flask server**

```bash
# From inside backend/
flask --app main run --debug
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser. The landing page means everything is working. The database file (`backend/library.db`) is created automatically on first start.

---

### First-Time Setup — Frontend

Open a **second terminal** for this — keep the Flask server running in the first one.

**Step 1 — Install Node packages**

```bash
cd frontend
npm install
```

This reads `frontend/package.json` and installs the Tailwind CSS compiler. It creates a `node_modules/` folder — that folder is large and is excluded from git, so you must run this after every fresh clone.

**Step 2 — Build the CSS**

```bash
# Still inside frontend/
npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css
```

This compiles `input.css` into `output.css`. The browser loads `output.css`. Never edit `output.css` by hand — it is overwritten on every build.

---

### Daily Development

Every time you sit down to work, you need **two terminals** running simultaneously.

**Terminal 1 — CSS watcher** (from `frontend/`)

```bash
source ../myenv/bin/activate      # macOS/Linux — skip if already active
npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css --watch
```

Leave this running. It automatically rebuilds the CSS whenever you save a template file.

**Terminal 2 — Flask server** (from `backend/`)

```bash
source ../myenv/bin/activate      # macOS/Linux — skip if already active
flask --app main run --debug
```

Leave this running too. The `--debug` flag auto-restarts the server whenever you save a Python file, so you rarely need to restart it manually.

---

## 4. Database Guide

### How the database is created

The database file (`backend/library.db`) is created automatically when the server starts for the first time. You do not need to create it yourself. Flask calls `init_db()` at startup, which runs `backend/schema.sql` to create all tables.

`schema.sql` uses `CREATE TABLE IF NOT EXISTS` everywhere, so it is safe to run on every startup — existing tables are left alone.

### Starter data

`schema.sql` also pre-loads four zones (Learning Plaza A/B, Computer Area, Quiet Study Room) and 26 seats with `INSERT OR IGNORE`, so the seed data only inserts once and is never duplicated on restart.

### Creating an admin account

The Sign Up page only creates student accounts. To create an admin, run this from `backend/` (with the virtual environment active):

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

Delete the database file and restart the server. It will be recreated from `schema.sql` with clean starter data.

```bash
# From the project root
rm backend/library.db
cd backend && flask --app main run --debug
```

---

## 5. Must-Know Concepts

You don't need to memorise all of this before touching the code. But reading it once will save you a lot of confusion when something breaks or when you need to add a feature.

---

### The three-layer architecture

The backend is organized into three distinct layers. Each layer has one job and talks only to the layer below it.

```
Browser request
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  ROUTES  (backend/routes/)                          │
│                                                     │
│  • Receives the browser's HTTP request              │
│  • Reads form fields and URL parameters             │
│  • Calls the matching controller function           │
│  • Sends the response back (HTML page or JSON)      │
└─────────────────────┬───────────────────────────────┘
                      │ calls
                      ▼
┌─────────────────────────────────────────────────────┐
│  CONTROLLERS  (backend/controllers/)                │
│                                                     │
│  • Contains all the "thinking" — the business rules │
│  • Validates data (is the duration 1–4 hours?)      │
│  • Calls db.py to read or write the database        │
│  • Returns plain data (True/False, a user row, etc.)│
│  • Never touches Flask — no render_template here    │
└─────────────────────┬───────────────────────────────┘
                      │ calls
                      ▼
┌─────────────────────────────────────────────────────┐
│  DATABASE HELPERS  (backend/db.py)                  │
│                                                     │
│  • Manages the SQLite connection                    │
│  • Runs SQL queries safely (prevents injection)     │
│  • Returns raw database rows                        │
└─────────────────────────────────────────────────────┘
```

**Where to look when something is wrong:**

| Symptom | Likely layer to check |
|---|---|
| Wrong page shown, redirect going nowhere | `routes/` |
| Booking succeeds but wrong seat is updated | `controllers/` |
| Database error, column not found | `db.py` or `schema.sql` |
| Page looks wrong, missing data | `frontend/templates/` |

---

### Why we split routes from controllers

Before this refactor, all the code for each page lived together in a single `main.py`. A route function would parse the request, apply business rules, query the database, *and* return the response — all in one place.

That works for small apps, but it gets painful quickly:

- **Hard to find things.** To change the booking rule (e.g., max 4 hours), you had to search through page-handling code to find where that number lives.
- **Hard to reuse logic.** If two pages both needed to check seat availability, you either duplicated the code or wrote a one-off helper inside `main.py`.
- **Hard to reason about errors.** A bug in booking logic was buried inside a function that also handled redirects and flash messages.

With the current split:

- **Routes** only care about HTTP — what came in, what goes out. They are thin wrappers.
- **Controllers** only care about business rules — they can be read and understood without knowing anything about Flask.

As a practical example, here is how booking works now:

```python
# routes/seats.py — only HTTP concerns
@seats_bp.route('/api/book', methods=['POST'])
@login_required
def api_book():
    seat_id      = request.form.get('seat_id', '').strip()   # parse
    booking_date = request.form.get('booking_date', '').strip()
    start_time   = request.form.get('start_time', '').strip()
    duration     = request.form.get('duration', '').strip()

    success, message = book_seat(                             # delegate
        session['user_id'], seat_id, booking_date, start_time, duration
    )
    if success:
        return jsonify(success=True, message=message)         # respond
    return jsonify(success=False, error=message)
```

```python
# controllers/seats.py — only business logic
def book_seat(user_id, seat_id, booking_date, start_time, duration):
    # validate inputs…
    # check seat exists and is available…
    # atomically claim the seat…
    # insert the reservation…
    return True, 'Seat booked successfully!'
```

The controller does not know what HTTP is. The route does not know what "atomically claiming a seat" means. Each part can be understood on its own.

---

### How authentication and access control work

**Session cookies** are how Flask remembers who you are between page loads. When you log in, Flask stores your student ID in a signed cookie in your browser:

```python
session['user_id'] = user['uId']   # set at login
session.clear()                    # wiped at logout
```

The cookie is **signed** with the `SECRET_KEY`, so its contents cannot be forged. We only store the student ID — never a password or full user object.

**Decorators** in `backend/decorators.py` guard every protected page. Adding `@login_required` above a route function is like putting a locked door in front of it:

```python
@seats_bp.route('/seat-map')
@login_required          # ← checked before the function runs
def seat_map():
    ...
```

`@login_required` performs three checks in order:

1. Is there a `user_id` in the session cookie?
2. Does that user ID still exist in the database? (Protects against deleted accounts.)
3. Is the account active, not suspended?

If any check fails, the user is redirected to the login page. `@admin_required` adds a fourth check: is the user's role set to `'admin'`?

---

### How page templates work

All HTML lives in `frontend/templates/`. Each file is a **template** — it has placeholders that Flask fills with real data before sending the page to your browser. Think of it like a form letter: the structure is fixed, but the name and details change each time.

Every page shares common elements (sidebar, navigation, header) through **template inheritance**. Instead of copying the sidebar HTML into every page file, each page just says "extend this parent" and fills in its unique section:

```html
{% extends "dashboard-layout.html" %}

{% block content %}
  <h1>Welcome, {{ current_user['uname'] }}!</h1>
{% endblock %}
```

`dashboard-layout.html` contains the sidebar, top navigation bar, logout confirmation dialog, and toast notifications. Change it once and every dashboard page is updated automatically.

**Reusable snippets** live in `frontend/templates/components/`. These are macros — HTML you call like a function:

```html
{% from "components/ui/button.html" import Button %}
{{ Button("Book Now", variant="primary") }}
```

Change the button style in one place, and it updates everywhere.

---

### How forms are protected

Forms have three layers of protection, from weakest to strongest:

1. **HTML `required` attribute** — stops the browser from submitting an empty field. Easy to bypass by editing the HTML, so never rely on this alone.

2. **Server-side validation** — `form.validate_on_submit()` re-checks every field in Python, even if someone bypassed the browser check. This is the real protection.

3. **CSRF token** — every form includes a hidden token generated by Flask-WTF. Without it, a malicious website could trick your browser into submitting a form on your behalf (a "Cross-Site Request Forgery" attack). The `{{ form.hidden_tag() }}` line in every template is what includes this token. Never remove it.

---

### How data is read from and written to the database

All direct database access goes through helpers in `backend/db.py`.

**Reading data** — use `query_db()`:

```python
# Fetch one row (returns None if nothing is found)
user = query_db('SELECT * FROM users WHERE uId = ?', (student_id,), one=True)

# Fetch all matching rows
seats = query_db('SELECT * FROM seats WHERE zoneId = ?', (zone_id,))
```

The `?` placeholder is critical — it prevents SQL injection by keeping your data separate from the SQL command. Never build SQL by joining strings together.

**Writing data** — use `get_db()` and always call `.commit()`:

```python
db = get_db()
db.execute('INSERT INTO users (uId, uname, password, role, ustatus) VALUES (?, ?, ?, ?, ?)',
           (student_id, full_name, hashed_password, 'user', 'active'))
db.commit()   # without this, the change is not saved to disk
```

---

## 6. Contributor Workflow

This section is a step-by-step guide for adding any new feature to the project. It exists because the most common mistake newcomers make is putting too much code in the wrong place — specifically, writing business logic directly inside a route. Following this sequence every time prevents that.

---

### The mental model: data → logic → delivery

Before you write a single line of code, think about your feature in three stages:

```
1. DATA      What does the database need to store or return?
                └─▶ Write a function in backend/controllers/

2. LOGIC     What rules apply? What can go wrong?
                └─▶ Write the checks inside that same controller function

3. DELIVERY  How does the browser ask for it, and what does it get back?
                └─▶ Write a thin route in backend/routes/
                └─▶ Write or update a template in frontend/templates/
```

A useful test for whether something belongs in a **controller**: can you read the function without knowing what Flask is? If it uses `request`, `render_template`, `session`, or `redirect`, it does not belong in a controller — those are delivery concerns.

A useful test for whether something belongs in a **route**: is it doing anything other than reading the request, calling a controller, and returning a response? If yes, move that part to a controller.

---

### Backend workflow

We will use a concrete example throughout: **cancelling a booking**. A student clicks "Cancel" on their booking, the reservation status changes to `'cancelled'`, and the seat is freed up.

---

**Step 1 — Write the controller function**

Open (or create) the relevant file under `backend/controllers/` and write a function that contains all the logic. This function must not import anything from Flask.

```python
# backend/controllers/seats.py

def cancel_booking(user_id, reservation_id):
    """Cancel a reservation if it belongs to the requesting user.

    Returns (True, success_msg) or (False, error_msg).
    """
    # Rule 1: does this reservation exist and belong to this user?
    reservation = query_db(
        'SELECT reservationId, seatId, status FROM reservations '
        'WHERE reservationId = ? AND uId = ?',
        (reservation_id, user_id),
        one=True
    )
    if not reservation:
        return False, 'Reservation not found.'

    # Rule 2: can only cancel active reservations.
    if reservation['status'] != 'active':
        return False, 'Only active reservations can be cancelled.'

    db = get_db()
    db.execute(
        "UPDATE reservations SET status = 'cancelled' WHERE reservationId = ?",
        (reservation_id,)
    )
    db.execute(
        "UPDATE seats SET status = 'available' WHERE seatId = ?",
        (reservation['seatId'],)
    )
    db.commit()
    return True, 'Booking cancelled successfully.'
```

Notice what this function does **not** do: it never touches `request`, `session`, `flash`, or `render_template`. It is pure logic that happens to use the database. You could call it from a test, a CLI script, or a scheduled job — not just an HTTP request.

---

**Step 2 — Register the route**

Open the relevant file under `backend/routes/` and write a thin route that does exactly three things: read the request, call the controller, return the response.

```python
# backend/routes/seats.py

@seats_bp.route('/api/cancel-booking', methods=['POST'])
@login_required
def cancel_booking_route():
    reservation_id = request.form.get('reservation_id', '').strip()  # 1. read

    success, message = cancel_booking(session['user_id'], reservation_id)  # 2. call

    if success:                                                        # 3. respond
        return jsonify(success=True, message=message)
    return jsonify(success=False, error=message)
```

That is the entire route function. Three lines of real logic. If you find yourself writing `if`/`else` business rules or SQL queries inside a route, stop — those belong in the controller.

> **Why import the controller function, not copy-paste the code?**
> Because next month, the cancellation rule will change ("only cancel 30 minutes before start time"). You will change it in one place — `controllers/seats.py` — and every route that calls `cancel_booking()` gets the fix for free.

---

### Frontend workflow

With the backend in place, here is how to build the UI that calls it.

---

**Step 3 — Check the component library before building anything new**

Look inside `frontend/templates/components/ui/` before writing any HTML from scratch. The project already has macros for buttons, inputs, icons, and dialogs. Reusing them keeps the UI consistent and saves you time.

```
frontend/templates/components/ui/
├── button.html        ← Button(label, variant, size)
├── input.html         ← Input(field)
├── icon.html          ← Icon(name, class)
├── alert-dialog.html  ← AlertDialog(id, title, …)
└── toast.html         ← ToastContainer()
```

Import a macro at the top of your template file before using it:

```html
{% from "components/ui/button.html" import Button %}
{% from "components/ui/icon.html" import Icon %}
```

---

**Step 4 — Create or update the template**

Either create a new file in `frontend/templates/dashboard/` or add to an existing one. For the cancel example, you would update `my-bookings.html` to include a cancel button on each booking card.

Every dashboard page must start by extending the shared layout, which gives you the sidebar, nav, and toasts automatically:

```html
{% extends "dashboard-layout.html" %}

{% block content %}
<div class="p-6 max-w-4xl mx-auto">

  {% for booking in bookings %}
    <div class="bg-card border border-border rounded-2xl p-4 flex items-center justify-between">

      <div>
        <p class="font-semibold text-foreground">Seat {{ booking.destNo }}</p>
        <p class="text-sm text-muted-foreground">{{ booking.startTime }} – {{ booking.endTime }}</p>
      </div>

      <!-- Cancel button — submits a form to the backend route -->
      <form method="POST" action="{{ url_for('seats.cancel_booking_route') }}">
        {{ csrf_token_field() }}
        <input type="hidden" name="reservation_id" value="{{ booking.reservationId }}">
        {{ Button("Cancel", variant="ghost", type="submit") }}
      </form>

    </div>
  {% endfor %}

</div>
{% endblock %}
```

Key details:
- `url_for('seats.cancel_booking_route')` uses the blueprint prefix `seats.` — never just `'cancel_booking_route'`.
- The hidden `reservation_id` field passes the ID to the route without exposing it as a URL parameter.
- The CSRF token field must be present on every form that modifies data.

---

**Step 5 — Pass data from the route to the template**

The controller returns raw data; the route passes it to the template. Update the route that renders `my-bookings.html` to fetch bookings and send them in:

```python
# backend/routes/seats.py

@seats_bp.route('/my-bookings')
@login_required
def my_bookings():
    bookings = get_user_bookings(session['user_id'])   # controller call
    return render_template("dashboard/my-bookings.html", bookings=bookings)
```

And in `backend/controllers/seats.py`, add the corresponding controller function:

```python
def get_user_bookings(user_id):
    return query_db(
        '''SELECT r.reservationId, r.startTime, r.endTime, r.status, s.destNo
           FROM reservations r
           JOIN seats s ON r.seatId = s.seatId
           WHERE r.uId = ? AND r.status = 'active'
           ORDER BY r.startTime''',
        (user_id,)
    )
```

The template uses `bookings` because that is what `render_template` received. The controller never touched a template, and the template never touched the database.

---

### The one rule you must not break

> **Business logic never goes in `routes/`.**

"Business logic" means: decisions, rules, validation, and database writes. The following code should make you stop and move it to a controller:

| If you see this inside a route file... | Move it to |
|---|---|
| An `if/else` that enforces a rule (e.g., "can only cancel active bookings") | `controllers/` |
| A raw SQL `UPDATE` or `INSERT` | `controllers/` |
| More than one call to `query_db()` | `controllers/` |
| Any calculation on data from the database | `controllers/` |

Routes are allowed to have one `if/else` — checking `success` and returning different responses. That is a delivery decision, not a business rule.

---

### Pre-PR checklist

Before you push your branch and open a pull request, run through this list:

- [ ] Every new SQL query lives in `backend/controllers/`, not in `backend/routes/`
- [ ] Every new route function has at most one `if/else` (the success/failure response split)
- [ ] New templates extend either `layout.html` or `dashboard-layout.html`
- [ ] All `url_for()` calls use the blueprint prefix (`auth.login`, `seats.seat_map`, `admin.admin_dashboard`, etc.)
- [ ] Every form that writes data includes a CSRF token field
- [ ] The virtual environment is active and `pip install -r requirements.txt` passes cleanly
- [ ] The CSS watcher has been running — `frontend/static/css/output.css` is up to date
- [ ] You have tested the page in the browser, not just read the code

---

## 7. Adding New Features

### New page

The new three-layer structure means a new page has three touch points: a controller function, a route, and a template.

**Step 1 — Add a controller function** in the relevant file under `backend/controllers/`:

```python
# backend/controllers/seats.py
def get_my_new_data():
    return query_db('SELECT * FROM some_table')
```

**Step 2 — Add a route** in the relevant file under `backend/routes/`:

```python
# backend/routes/seats.py
@seats_bp.route('/my-new-page')
@login_required
def my_new_page():
    data = get_my_new_data()                             # call controller
    return render_template("dashboard/my-new-page.html", data=data)  # render
```

**Step 3 — Create the template** at `frontend/templates/dashboard/my-new-page.html`:

```html
{% extends "dashboard-layout.html" %}
{% block content %}
  <h1>My New Page</h1>
{% endblock %}
```

**Step 4 — Add a nav link** (optional) in `frontend/templates/dashboard-layout.html`:

```jinja
set nav_items = [
    ...
    {'endpoint': 'seats.my_new_page', 'label': 'My Page', 'icon': 'some-icon'},
]
```

### New form

1. Add a form class in `backend/forms/auth.py` (or a new file in `backend/forms/`).
2. Export it from `backend/forms/__init__.py`.
3. Import and instantiate it in the relevant **route** file, then pass it to `render_template`.
4. Add business logic for handling the submission to the matching **controller** file.
5. In the template, always include `{{ form.hidden_tag() }}` as the first line inside `<form>`.

### New database table

1. Add `CREATE TABLE IF NOT EXISTS ...` to `backend/schema.sql`.
2. Add any starter rows with `INSERT OR IGNORE`.
3. Delete `backend/library.db` and restart the server so the new table is created.
4. Add query functions to `backend/controllers/` as needed.

---

## 8. Troubleshooting

| What you see | Why it happens | How to fix it |
|---|---|---|
| `RuntimeError: No application found` | A Python file was run outside Flask's context | Run via `flask --app main run` from `backend/`, or wrap the code in `with app.app_context():` |
| `BuildError: Could not build url for endpoint 'login'` | A template or redirect still uses an old un-prefixed endpoint name | Endpoint names now use blueprint prefixes: `auth.login`, `seats.seat_map`, `admin.admin_dashboard`, etc. |
| `400 Bad Request` on a form submission | The CSRF token is missing | Ensure `{{ form.hidden_tag() }}` is the first element inside your `<form>` tag |
| Page looks completely unstyled | The Tailwind output file was not built | Run the build command from `frontend/`, or start watch mode |
| Changes to Python files are not reflected | The virtual environment is not active | Check that `(myenv)` appears in your terminal prompt; re-run `source myenv/bin/activate` if not |
| Old schema after adding a new table | The database file predates your change | Delete `backend/library.db` and restart the server |
| `OperationalError: no such table` | The database was not initialized | Ensure the server starts without errors; `init_db()` runs automatically on startup |
| Login redirects back to the login page forever | You are already logged in | Clear browser cookies, or open a private/incognito window |
