from flask import Blueprint, render_template, redirect, url_for, session, flash
from forms import LoginForm, SignUpForm
from controllers.auth import authenticate_user, register_user

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('seats.user_dashboard'))

    form    = LoginForm()
    message = ""

    if form.validate_on_submit():
        user, error = authenticate_user(form.student_id.data, form.password.data)
        if error:
            message = error
        else:
            session['user_id'] = user['uId']
            flash(f'Welcome back, {user["uname"]}!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('seats.user_dashboard'))

    return render_template("auth/login.html", form=form, message=message)


@auth_bp.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if 'user_id' in session:
        return redirect(url_for('seats.user_dashboard'))

    form    = SignUpForm()
    message = ""

    if form.validate_on_submit():
        success, error = register_user(
            form.student_id.data,
            form.full_name.data,
            form.phone_no.data or '',
            form.password.data,
        )
        if error:
            message = error
        else:
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))

    return render_template("auth/sign-up.html", form=form, message=message)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
