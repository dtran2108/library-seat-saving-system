"""
forms/auth.py — WTForms form classes for user authentication.

LoginForm:  Student ID + Password
SignUpForm: Student ID + Full Name + Phone Number + Password + Confirm Password
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo


class LoginForm(FlaskForm):
    """Login form — students log in using their Student ID and password."""
    student_id = StringField('Student ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class SignUpForm(FlaskForm):
    """
    Sign-up form — collects all fields needed to create a new student account.
    
    Maps to the ER model's User entity:
        student_id       → uId (primary key)
        full_name        → uname
        phone_no         → phoneNo
        password         → password (will be hashed before storing)
        confirm_password → validation only (not stored)
    """
    student_id = StringField('Student ID', validators=[
        DataRequired(),
        Length(min=1, max=20, message='Student ID must be between 1 and 20 characters.')
    ])
    full_name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=1, max=100, message='Full name must be between 1 and 100 characters.')
    ])
    phone_no = StringField('Phone Number')
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Create Account')