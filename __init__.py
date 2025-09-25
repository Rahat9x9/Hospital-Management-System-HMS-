from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ✅ Define extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    # Error handler for 403 Forbidden (must be after app is created)
    # Remove error handler registration from here
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey1234')

    # Allow overriding the full DB URI (useful for testing with SQLite)
    env_db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
    if env_db_uri:
        app.config['SQLALCHEMY_DATABASE_URI'] = env_db_uri
    else:
        DB_USER = os.getenv('DB_USERNAME', 'root')
        DB_PASSWORD = os.getenv('DB_PASSWORD', '')
        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_NAME = os.getenv('DB_NAME', 'hms')
        DB_PORT = os.getenv('DB_PORT', '3306')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ✅ Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # ✅ Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.patients import patients_bp
    from app.routes.wards import wards_bp
    from app.routes.teams import teams_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.doctor import doctor_bp
    from app.routes.nurse import nurse_bp
    from app.routes.staff import staff_bp
    # Debug routes (only register when app.debug)
    from app.routes.debug import debug_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(wards_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(nurse_bp)
    app.register_blueprint(staff_bp)
    if app.debug:
        app.register_blueprint(debug_bp)


    with app.app_context():
        from app.models import create_default_users
        create_default_users()

    app_returned = app
    def forbidden(e):
        return render_template('403.html'), 403
    app_returned.register_error_handler(403, forbidden)
    return app_returned

# ✅ Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))
