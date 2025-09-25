from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Doctor, Patient, TreatmentLog

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/doctor')
@login_required
def dashboard():
    if not (current_user.is_authenticated and (current_user.role or '').lower() == 'doctor'):
        from flask import abort
        abort(403)
    # Find doctor record for current user
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    my_patients = []
    todays_appointments = []
    rounds_scheduled = 0
    from datetime import datetime, UTC
    today = datetime.now(UTC).date()
    if doctor:
        # Patients assigned to this doctor's team
        my_patients = Patient.query.filter_by(team_id=doctor.team_id).order_by(Patient.admission_date.desc()).all()
        # Example: Appointments are treatments scheduled for today
        todays_appointments = [
            {
                'patient_name': t.patient.name if t.patient else '',
                'time': t.treatment_time.strftime('%H:%M'),
                'ward': t.patient.assigned_ward.name if t.patient and t.patient.assigned_ward else '',
                'notes': t.notes or ''
            }
            for t in TreatmentLog.query.filter_by(doctor_id=doctor.id).filter(
                TreatmentLog.treatment_time >= datetime(today.year, today.month, today.day, tzinfo=UTC),
                TreatmentLog.treatment_time < datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=UTC)
            ).all()
        ]
        rounds_scheduled = len(todays_appointments)
    return render_template(
        'doctor/dashboard.html',
        doctor=doctor,
        my_patients=my_patients,
        todays_appointments=todays_appointments,
        rounds_scheduled=rounds_scheduled
    )
