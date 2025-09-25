from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def roles_required(*allowed_roles):
    """Decorator to require that current_user has one of the allowed roles.

    Usage:
        @roles_required('admin', 'staff')
        def view():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user or not getattr(current_user, 'is_authenticated', False):
                flash('Authentication required.', 'danger')
                return redirect(url_for('auth.login'))
            if allowed_roles and getattr(current_user, 'role', None) not in allowed_roles:
                flash('You do not have permission to perform this action.', 'danger')
                return redirect(url_for('patients.list_patients'))
            return f(*args, **kwargs)
        return wrapped
    return decorator
