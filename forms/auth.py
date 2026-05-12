"""
forms/auth.py — WTForms form classes for user authentication.

LoginForm:  Student ID + Password
SignUpForm: Student ID + Full Name + Phone Number + Password + Confirm Password

render_kw notes:
  - required=True  adds the HTML `required` attribute so browsers enforce
    presence before the form is ever submitted (first line of defence).
  - placeholder     gives users a concrete example of the expected value.
  Fields without DataRequired() deliberately omit required=True.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo


class LoginForm(FlaskForm):
    """Login form — students log in using their Student ID and password."""

    student_id = StringField(
        'Student ID',
        validators=[DataRequired()],
        render_kw={'required': True, 'placeholder': 'e.g. B123456789'},
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()],
        render_kw={'required': True, 'placeholder': '••••••••'},
    )
    submit = SubmitField('Login')


class SignUpForm(FlaskForm):
    """
    Sign-up form — collects all fields needed to create a new student account.

    Maps to the ER model's User entity:
        student_id       → uId (primary key)
        full_name        → uname
        phone_no         → phoneNo        (optional)
        password         → password       (hashed before storing)
        confirm_password → validation only (not stored)
    """

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
            EqualTo('password', message='Passwords must match.'),
        ],
        render_kw={'required': True, 'placeholder': 'Repeat your password'},
    )
    submit = SubmitField('Create Account')
