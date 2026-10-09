"""
Authentication routes for login, registration, and logout.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from app.extensions import db
from app.models import User, UserRole

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login supporting Student, Staff, and Administrator."""
    if g.current_user:
        if g.current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif g.current_user.is_staff:
            return redirect(url_for('staff.dashboard'))
        return redirect(url_for('student.menu'))

    if request.method == 'POST':
        identifier = (request.form.get('identifier') or '').strip()
        password = request.form.get('password') or ''
        next_url = request.form.get('next') or request.args.get('next')

        if not identifier or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template('login.html', identifier=identifier, next=next_url)

        # Lookup by username OR email
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if not user or not user.check_password(password):
            flash("Invalid credentials. Please verify your login details.", "danger")
            return render_template('login.html', identifier=identifier, next=next_url)

        if not user.is_active:
            flash("Your account has been deactivated. Please contact food court administration.", "danger")
            return render_template('login.html', identifier=identifier, next=next_url)

        # Establish secure session
        session.clear()
        session['user_id'] = user.id
        session.permanent = True

        flash(f"Welcome back, {user.full_name}!", "success")

        if next_url and next_url.startswith('/'):
            return redirect(next_url)

        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif user.is_staff:
            return redirect(url_for('staff.dashboard'))
        else:
            return redirect(url_for('student.menu'))

    return render_template('login.html', next=request.args.get('next'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Student account registration."""
    if g.current_user:
        return redirect(url_for('student.menu'))

    if request.method == 'POST':
        full_name = (request.form.get('full_name') or '').strip()
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        phone = (request.form.get('phone') or '').strip()
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        # Validation
        if not full_name or not username or not email or not password:
            flash("All required fields must be completed.", "danger")
            return render_template('register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash("Username is already taken. Please choose another one.", "danger")
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash("Email is already registered. Please sign in.", "warning")
            return redirect(url_for('auth.login'))

        # Create new student
        new_student = User(
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
            role=UserRole.STUDENT,
            is_active=True
        )
        new_student.set_password(password)

        db.session.add(new_student)
        db.session.commit()

        # Automatically log in the student
        session.clear()
        session['user_id'] = new_student.id
        session.permanent = True

        flash("Account created successfully! Welcome to Smart Food Court.", "success")
        return redirect(url_for('student.menu'))

    return render_template('register.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Sign out current user and clear session."""
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('student.home'))
