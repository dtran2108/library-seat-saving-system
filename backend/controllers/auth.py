from werkzeug.security import generate_password_hash, check_password_hash
from db import query_db, get_db


def authenticate_user(student_id, password):
    """Validate credentials. Returns (user_row, None) on success or (None, error_str) on failure."""
    user = query_db('SELECT * FROM users WHERE uId = ?', (student_id,), one=True)
    if user and check_password_hash(user['password'], password):
        if user['ustatus'] == 'suspended':
            return None, "Your account has been suspended. Please contact the library staff."
        return user, None
    # Same message for wrong ID and wrong password — don't leak which one failed.
    return None, "Invalid Student ID or password."


def register_user(student_id, full_name, phone_no, password):
    """Create a new user. Returns (True, None) on success or (False, error_str) on failure."""
    existing = query_db('SELECT uId FROM users WHERE uId = ?', (student_id,), one=True)
    if existing:
        return False, "An account with this Student ID already exists."

    hashed_password = generate_password_hash(password)
    db = get_db()
    db.execute(
        'INSERT INTO users (uId, uname, phoneNo, password, role, ustatus) VALUES (?, ?, ?, ?, ?, ?)',
        (student_id, full_name, phone_no, hashed_password, 'user', 'active')
    )
    db.commit()
    return True, None
