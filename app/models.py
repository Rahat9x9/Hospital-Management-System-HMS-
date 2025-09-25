# ---------------------------
# Nurse model
# --------------------------
from app import db, login_manager
class Nurse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(50))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)

    def __repr__(self):
        return f'<Nurse {self.name}>'
# ---------------------------
# Technician model
# ---------------------------
class Technician(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)

    def __repr__(self):
        return f'<Technician {self.name} ({self.specialization})>'
from sqlalchemy.orm import validates
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC
# ---------------------------
# TreatmentLog model (FR5)
# ---------------------------
class TreatmentLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)

    treatment_time = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)
    notes = db.Column(db.Text)
    medication = db.Column(db.String(255))
    dosage = db.Column(db.String(100))
    nurse_id = db.Column(db.Integer, db.ForeignKey('nurse.id'))

    patient = db.relationship('Patient', backref='treatment_logs')
    doctor = db.relationship('Doctor', backref='treatment_logs')
    nurse = db.relationship('Nurse', backref='treatment_logs')

    def __repr__(self):
        return f'<TreatmentLog Patient {self.patient_id} Doctor {self.doctor_id}>'

# ActivityLog model for professional recent activity tracking
class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(64))
    action = db.Column(db.String(64))
    details = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ActivityLog {self.action} by {self.username} at {self.timestamp}>'
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# ---------------------------
# User model
# ---------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if 'password' in kwargs:
            self.set_password(kwargs['password'])

    def set_password(self, password):
        if not password:
            raise ValueError("Password cannot be empty")
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=16
        )

    def check_password(self, password):
        if not self.password_hash:
            return False
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            return False

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    from app import db
    return db.session.get(User, int(user_id))


# ---------------------------
# Ward model
# ---------------------------
class Ward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    current_occupancy = db.Column(db.Integer, default=0, nullable=False)
    patients = db.relationship('Patient', backref='assigned_ward', lazy=True)

    def available_beds(self):
        return self.capacity - self.current_occupancy

    def __repr__(self):
        return f'<Ward {self.name}>'


# ---------------------------
# Team model
# ---------------------------
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    doctors = db.relationship('Doctor', backref='medical_team', lazy=True)
    patients = db.relationship('Patient', backref='treatment_team', lazy=True)

    def __repr__(self):
        return f'<Team {self.code} - {self.name}>'


# ---------------------------
# Doctor model
# ---------------------------
class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(20), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)

    def __repr__(self):
        return f'<Doctor {self.name} ({self.specialization})>'

    @staticmethod
    def normalize_grade(grade_str: str) -> str:
        """Return a canonical grade string for storage.

        Rules (simple heuristics):
        - If contains 'consult' -> 'Consultant'
        - If contains 'grade 1', 'grade1', 'g1', 'junior' -> 'Grade 1'
        - Otherwise return stripped title-cased string
        """
        if not grade_str:
            return ''
        g = grade_str.strip().lower()
        import re
        if re.search(r'consult', g):
            return 'Consultant'
        if re.search(r'grade\s*1|grade1|\bg1\b|junior', g):
            return 'Grade 1'
        # Fallback: Title-case trimmed
        return grade_str.strip().title()

    @validates('grade')
    def _normalize_grade_on_set(self, key, value):
        # When grade is assigned, normalize it for consistent storage
        return Doctor.normalize_grade(value)


# ---------------------------
# Patient model
# ---------------------------
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_identifier = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    admission_date = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)
    discharge_date = db.Column(db.DateTime)
    ward_id = db.Column(db.Integer, db.ForeignKey('ward.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    medical_record = db.Column(db.Text)

    def is_discharged(self):
        return self.discharge_date is not None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not getattr(self, 'patient_identifier', None):
            # Generate a unique identifier like P0001, P0002, ...
            last = Patient.query.order_by(Patient.id.desc()).first()
            next_num = (last.id + 1) if last else 1
            self.patient_identifier = f"P{next_num:04d}"

    def __repr__(self):
        return f'<Patient {self.name}>'
from app import db
from app.models import User
from werkzeug.security import generate_password_hash

def create_default_users():
    default_users = [
        {
            'username': 'admin',
            'email': 'admin@hospital.com',
            'role': 'admin',
            'password': 'admin123'
        },
        {
            'username': 'nurse',
            'email': 'nurse@hospital.com',
            'role': 'nurse',
            'password': 'nurse123'
        },
        {
            'username': 'doctor',
            'email': 'doctor@hospital.com',
            'role': 'doctor',
            'password': 'doctor123'
        }
    ]
    for user_data in default_users:
        user = User.query.filter_by(username=user_data['username']).first()
        if not user:
            new_user = User(
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
            )
            new_user.set_password(user_data['password'])
            db.session.add(new_user)
    db.session.commit()


