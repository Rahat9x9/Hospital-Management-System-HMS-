from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app.models import User
from app import db
from urllib.parse import urlparse, urljoin

auth_bp = Blueprint('auth', __name__)

def is_safe_url(target):
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return redirect_url.scheme in ('http', 'https') and host_url.netloc == redirect_url.netloc

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            # Redirect based on role
            role = (user.role or '').lower()
            if role == 'admin':
                return redirect(url_for('dashboard.dashboard'))
            elif role == 'doctor':
                return redirect(url_for('doctor.dashboard'))
            elif role == 'nurse':
                return redirect(url_for('nurse.dashboard'))
            else:
                flash('Unknown user role. Please contact administrator.', 'danger')
                logout_user()
                return redirect(url_for('auth.login'))
        flash('Invalid username or password', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
