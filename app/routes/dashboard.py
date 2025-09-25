# -----------------------------
# Route: Billing
# -----------------------------

# Move billing route below dashboard_bp definition

# -----------------------------
# Route: Doctor Scheduling
# -----------------------------

# Move doctor_scheduling route below dashboard_bp definition

# app/routes/dashboard.py

from flask import Blueprint, render_template, jsonify, abort
from flask_login import login_required, current_user
from app.models import Patient, TreatmentLog, Doctor, ActivityLog
from app.models import Patient, Ward, Team, Doctor, TreatmentLog, ActivityLog
from app.models import Nurse
from datetime import datetime, UTC, timedelta
from collections import OrderedDict
import os

# Blueprint definition — only once
dashboard_bp = Blueprint('dashboard', __name__)
@dashboard_bp.route('/reports', methods=['GET'])
@login_required
def reports():
    if current_user.role != 'admin':
        abort(403)
    total_patients = Patient.query.count()
    total_treatments = TreatmentLog.query.count()
    # Example: income estimate = $100 per treatment
    income_estimate = total_treatments * 100
    treatments = TreatmentLog.query.order_by(TreatmentLog.treatment_time.desc()).limit(20).all()
    return render_template('dashboard/reports.html',
                           total_patients=total_patients,
                           total_treatments=total_treatments,
                           income_estimate=income_estimate,
                           treatments=treatments)

# Path for notifications audit log
AUDIT_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'audit.log')

# -----------------------------
# Route: Admin Dashboard
# -----------------------------
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    if not (current_user.is_authenticated and (current_user.role or '').lower() == 'admin'):
        abort(403)

    total_patients = Patient.query.count()

    total_beds = sum(ward.capacity for ward in Ward.query.all())
    occupied_beds = sum(ward.current_occupancy for ward in Ward.query.all())
    available_beds = total_beds - occupied_beds

    active_teams = Team.query.count()

    today = datetime.now(UTC).date()
    discharged_patients = Patient.query.filter(
        Patient.discharge_date != None,
        Patient.discharge_date >= datetime(today.year, today.month, today.day),
        Patient.discharge_date < datetime(today.year, today.month, today.day, 23, 59, 59)
    ).count()

    total_doctors = Doctor.query.count()
    total_nurses = Nurse.query.count()
    stats = {
        'total_patients': total_patients,
        'total_beds': total_beds,
        'available_beds': available_beds,
        'active_teams': active_teams,
        'discharged_patients': discharged_patients,
        'total_doctors': total_doctors,
        'total_nurses': total_nurses,
    }

    recent_patients = Patient.query.order_by(Patient.admission_date.desc()).limit(5).all()
    recent_treatments = TreatmentLog.query.order_by(TreatmentLog.treatment_time.desc()).limit(5).all()
    doctors = Doctor.query.order_by(Doctor.name).limit(6).all()
    # Recent activity: last 10 actions
    recent_activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()

    # Treatments per last 7 days
    start_date = today - timedelta(days=6)
    treatments_recent = TreatmentLog.query.filter(
        TreatmentLog.treatment_time >= datetime(start_date.year, start_date.month, start_date.day, tzinfo=UTC)
    ).all()

    counts = OrderedDict(( (start_date + timedelta(days=i)).strftime('%Y-%m-%d'), 0 ) for i in range(7))
    for t in treatments_recent:
        key = t.treatment_time.astimezone(UTC).date().strftime('%Y-%m-%d')
        if key in counts:
            counts[key] += 1
    treatments_chart = {'labels': list(counts.keys()), 'data': list(counts.values())}

    total_treatments = TreatmentLog.query.count()
    income_estimate = total_treatments * 120  # Simple estimate

    wards = Ward.query.all()
    ward_chart = {'labels': [w.name for w in wards], 'data': [w.current_occupancy for w in wards]}

    from app.models import Technician
    staff_chart = {'labels': [w.name for w in wards], 'data': []}
    for w in wards:
        doctor_ids = set()
        nurse_ids = set()
        technician_ids = set()
        for p in getattr(w, 'patients', []):
            if hasattr(p, 'team_id') and p.team_id:
                team = Team.query.get(p.team_id)
                if team:
                    for d in getattr(team, 'doctors', []):
                        doctor_ids.add(d.id)
        # Count technicians assigned to this ward (if you have such logic, otherwise count all)
        # If technicians are not assigned to wards, count all technicians
        technicians = Technician.query.all()
        technician_count = len(technicians)
        staff_chart['data'].append(len(doctor_ids) + len(nurse_ids) + technician_count)

    recent_admissions = Patient.query.order_by(Patient.admission_date.desc()).limit(5).all()
    recent_discharges = Patient.query.filter(Patient.discharge_date != None).order_by(Patient.discharge_date.desc()).limit(5).all()
    recent_staff_changes = []  # Optional

    # Pending treatments: treatments in last 7 days with status 'pending' (if status field exists)
    pending_treatments = []
    if hasattr(TreatmentLog, 'status'):
        pending_treatments = TreatmentLog.query.filter_by(status='pending').all()
    # Pass wards for alerts section
    wards = Ward.query.all()
    # Filter full wards in Python for template use
    full_wards = [w for w in wards if w.current_occupancy >= w.capacity]
    return render_template(
        'dashboard.html', stats=stats, recent_patients=recent_patients,
        recent_treatments=recent_treatments, doctors=doctors,
        treatments_chart=treatments_chart, income_estimate=income_estimate,
        ward_chart=ward_chart, staff_chart=staff_chart,
        recent_admissions=recent_admissions, recent_discharges=recent_discharges,
        recent_staff_changes=recent_staff_changes,
        current_year=datetime.now().year,
        wards=wards,
        full_wards=full_wards,
        pending_treatments=pending_treatments,
        recent_activities=recent_activities
    )

# -----------------------------
# Route: Medical Records
# -----------------------------
@dashboard_bp.route('/medical-records')
@login_required
def medical_records():
    if current_user.role.lower() not in ['admin', 'doctor', 'nurse']:
        abort(403)
    # TODO: Fetch real records
    records = []
    return render_template('records/medical_records.html', records=records)

# -----------------------------
# Route: Notifications
# -----------------------------
@dashboard_bp.route('/dashboard/notifications')
@login_required
def notifications():
    notifications = []
    try:
        if os.path.exists(AUDIT_LOG_PATH):
            with open(AUDIT_LOG_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-10:]
                for line in reversed(lines):
                    if 'INFO' in line:
                        msg = line.split('INFO', 1)[-1].strip()
                        notifications.append(msg)
    except Exception as e:
        notifications.append(f'Error reading audit log: {e}')
    return jsonify({'count': len(notifications), 'items': notifications})

@dashboard_bp.route('/doctor-scheduling')
@login_required
def doctor_scheduling():
    role = (current_user.role or '').lower()
    if role not in ['doctor', 'admin']:
        abort(403)
    from app.models import Doctor, Patient, TreatmentLog, Ward
    from sqlalchemy import or_
    from datetime import datetime, UTC
    selected_date = datetime.now(UTC).date()
    # Fetch appointments for today (using TreatmentLog as Appointment model)
    appointments_query = TreatmentLog.query.filter(
        TreatmentLog.treatment_time >= datetime(selected_date.year, selected_date.month, selected_date.day, tzinfo=UTC),
        TreatmentLog.treatment_time < datetime(selected_date.year, selected_date.month, selected_date.day, 23, 59, 59, tzinfo=UTC)
    ).order_by(TreatmentLog.treatment_time.asc())
    appointments = []
    for appt in appointments_query:
        appointments.append({
            'patient_name': appt.patient.name,
            'doctor_name': appt.doctor.name,
            'specialty': appt.doctor.specialization,
            'status': 'confirmed',  # You can add status field to TreatmentLog for real status
            'type': 'consultation', # You can add type field to TreatmentLog for real type
            'start_time': appt.treatment_time.strftime('%I:%M %p'),
            'duration': 30, # You can add duration field to TreatmentLog for real duration
        })
    # Fetch all doctors
    doctors_query = Doctor.query.order_by(Doctor.name).all()
    doctors = []
    for doc in doctors_query:
        doctors.append({
            'name': doc.name,
            'specialty': doc.specialization,
            'availability': 'Available', # You can add availability logic here
        })
    stats = {
        'total_today': len(appointments),
        'confirmed': len([a for a in appointments if a['status'] == 'confirmed']),
        'pending': len([a for a in appointments if a['status'] == 'pending']),
        'cancelled': len([a for a in appointments if a['status'] == 'cancelled']),
    }
    return render_template('dashboard/doctor_scheduling.html', appointments=appointments, doctors=doctors, stats=stats, selected_date=selected_date)

@dashboard_bp.route('/billing')
@login_required
def billing():
    role = (current_user.role or '').lower()
    if role not in ['doctor', 'admin']:
        abort(403)
    bills = [
        {
            'patient_name': 'John Doe',
            'service': 'Consultation',
            'amount': 120,
            'date': '2025-01-15',
            'status': 'Paid',
        },
        {
            'patient_name': 'Jane Smith',
            'service': 'Follow-up',
            'amount': 80,
            'date': '2025-01-15',
            'status': 'Pending',
        },
        {
            'patient_name': 'Robert Johnson',
            'service': 'Procedure',
            'amount': 300,
            'date': '2025-01-15',
            'status': 'Paid',
        },
    ]
    total_billed = sum(b['amount'] for b in bills)
    return render_template('dashboard/billing.html', bills=bills, total_billed=total_billed)
