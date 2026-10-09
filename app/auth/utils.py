"""
Authentication decorators and security helper functions.
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request, abort, g
from app.models import User, UserRole


def login_required(f):
    """Requires user to be logged in with any role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.current_user:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Requires user to have Administrator role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.current_user:
            flash("Administrator login required.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        if not g.current_user.is_admin:
            flash("Access denied: Administrator privileges required.", "danger")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def staff_required(f):
    """Requires user to have Staff or Administrator role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.current_user:
            flash("Staff login required.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        if not g.current_user.is_staff:
            flash("Access denied: Staff privileges required.", "danger")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
