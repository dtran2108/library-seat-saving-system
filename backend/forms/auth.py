# forms/auth.py — form definitions for login and sign-up.
#
# Defining forms in Python (rather than raw HTML) gives us two things:
#   - Server-side validation that runs even if someone bypasses the browser.
#   - A CSRF token baked in automatically via FlaskForm.

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo


class LoginForm(FlaskForm):

    student_id = StringField(
        'Student ID',
        validators=[DataRequired()],
        # `required=True` adds an HTML attribute that makes the browser refuse
        # to submit the form if the field is empty — a fast first check.
        # DataRequired() above is the server-side backup for the same rule.
        render_kw={'required': True, 'placeholder': 'e.g. B123456789'},
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()],
        render_kw={'required': True, 'placeholder': '••••••••'},
    )
    submit = SubmitField('Login')


class SignUpForm(FlaskForm):
    # Field names below map to the database columns in the users table:
    #   student_id  → uId (primary key)
    #   full_name   → uname
    #   phone_no    → phoneNo  (optional — no DataRequired validator)
    #   password    → stored as a hash, never the raw value
    #   confirm_password → used only for validation, never stored

    student_id = StringField(
        'Student ID',
        validators=[
            DataRequired(),
            Length(min=10, message='Student ID must be at least 10 characters.'),
        ],
        render_kw={'required': True, 'placeholder': 'e.g. B123456789'},
    )
    full_name = StringField(
        'Full Name',
        validators=[
            DataRequired(),
            Length(min=1, max=100, message='Full name must be between 1 and 100 characters.'),
        ],
        render_kw={'required': True, 'placeholder': 'Your full name'},
    )
    phone_no = StringField(
        'Phone Number',
        # No DataRequired here — phone number is optional, so we also omit
        # required=True from render_kw to avoid the browser enforcing it.
        render_kw={'placeholder': '0912-345-678 (optional)'},
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=6, message='Password must be at least 6 characters.'),
        ],
        render_kw={'required': True, 'placeholder': 'At least 6 characters'},
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            # EqualTo compares this field's value to another field's value at
            # submission time.
            EqualTo('password', message='Passwords must match.'),
        ],
        render_kw={'required': True, 'placeholder': 'Repeat your password'},
    )
    submit = SubmitField('Create Account')
