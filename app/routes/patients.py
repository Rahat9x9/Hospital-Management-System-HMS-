# ...existing code...

from flask import Blueprint, render_template, redirect, url_for, flash, request
import logging
from flask_login import login_required, current_user
from datetime import datetime, UTC
from app.models import Patient, Ward, Team, ActivityLog
from app import db
from app.utils import roles_required


# Audit logger setup
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)
audit_handler = logging.FileHandler('audit.log')
audit_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
if not audit_logger.hasHandlers():
    audit_logger.addHandler(audit_handler)

patients_bp = Blueprint('patients', __name__)

# List patients by ward (FR6)
@patients_bp.route('/wards/<int:ward_id>/patients')
@login_required
def list_patients_by_ward(ward_id):
    ward = Ward.query.get_or_404(ward_id)
    patients = Patient.query.filter_by(ward_id=ward_id).all()
    return render_template('patients/list_by_ward.html', ward=ward, patients=patients)

# List patients by team (FR7)
@patients_bp.route('/teams/<int:team_id>/patients')
@login_required
def list_patients_by_team(team_id):
    team = Team.query.get_or_404(team_id)
    patients = Patient.query.filter_by(team_id=team_id).all()
    return render_template('patients/list_by_team.html', team=team, patients=patients)

patients_bp = Blueprint('patients', __name__)

# Add patient form page (GET)
@patients_bp.route('/patients/add', methods=['GET'])
@login_required
@roles_required('admin', 'staff')
def add_patient_form():
    wards = Ward.query.all()
    teams = Team.query.all()
    current_date = datetime.now(UTC).strftime('%Y-%m-%d')
    return render_template('patients/add.html', wards=wards, teams=teams, current_date=current_date)

# Edit patient route (admin/staff)
@patients_bp.route('/patients/<int:id>/edit', methods=['POST'])
@login_required
@roles_required('admin', 'staff')
def edit_patient(id):
    patient = Patient.query.get_or_404(id)
    name = request.form.get('name')
    age = request.form.get('age')
    gender = request.form.get('gender')
    ward_id = request.form.get('ward_id')
    team_id = request.form.get('team_id')
    admission_date = request.form.get('admission_date')
    if not (name and age and gender and ward_id and team_id and admission_date):
        flash('All fields are required.', 'danger')
        return redirect(url_for('patients.list_patients'))
    ward = Ward.query.get(int(ward_id))
    if not ward:
        flash('Selected ward does not exist.', 'danger')
        return redirect(url_for('patients.list_patients'))
    # Capacity validation (allow if patient is already in this ward, or if beds available)
    if ward.id != patient.ward_id and ward.available_beds() < 1:
        flash('Selected ward has no available beds.', 'danger')
        return redirect(url_for('patients.list_patients'))
    try:
        admission_date_obj = datetime.strptime(admission_date, '%Y-%m-%d')
    except Exception:
        admission_date_obj = datetime.now(UTC)
    patient.name = name
    patient.age = int(age)
    patient.gender = gender
    # If changing ward, update occupancy
    if ward.id != patient.ward_id:
        old_ward = patient.assigned_ward
        if old_ward:
            old_ward.current_occupancy = max(0, old_ward.current_occupancy - 1)
        ward.current_occupancy = ward.current_occupancy + 1
        patient.ward_id = ward.id
    patient.team_id = int(team_id)
    patient.admission_date = admission_date_obj
    db.session.commit()
    flash('Patient updated successfully.', 'success')
    return redirect(url_for('patients.list_patients'))

# Transfer patient route (admin/staff)
@patients_bp.route('/patients/<int:id>/transfer', methods=['POST'])
@login_required
@roles_required('admin', 'staff')
def transfer_patient(id):
    patient = Patient.query.get_or_404(id)
    new_ward_id = request.form.get('new_ward_id')
    if not new_ward_id:
        flash('No ward selected.', 'danger')
        return redirect(url_for('patients.list_patients'))
    new_ward = Ward.query.get(int(new_ward_id))
    if not new_ward:
        flash('Selected ward does not exist.', 'danger')
        return redirect(url_for('patients.list_patients'))
    # Gender compatibility check (if ward is gendered)
    if new_ward.type.lower() in ['male', 'female']:
        if new_ward.type.lower() != patient.gender.lower():
            flash('Cannot transfer: Gender mismatch for ward.', 'danger')
            return redirect(url_for('patients.list_patients'))
    # Capacity validation
    if new_ward.available_beds() < 1:
        flash('Selected ward has no available beds.', 'danger')
        return redirect(url_for('patients.list_patients'))
    # Update occupancy: decrement old, increment new
    old_ward = patient.assigned_ward
    if old_ward:
        old_ward.current_occupancy = max(0, old_ward.current_occupancy - 1)
    new_ward.current_occupancy = new_ward.current_occupancy + 1
    patient.ward_id = new_ward.id
    db.session.commit()
    # Audit log
    audit_logger.info(f"User '{getattr(current_user, 'username', 'unknown')}' transferred patient '{patient.name}' (ID: {patient.id}) from ward '{old_ward.name if old_ward else 'unknown'}' (ID: {old_ward.id if old_ward else 'unknown'}) to ward '{new_ward.name}' (ID: {new_ward.id})")
    # Activity log
    activity = ActivityLog(
        user_id=getattr(current_user, 'id', None),
        username=getattr(current_user, 'username', 'unknown'),
        action='Transfer Patient',
        details=f"{patient.name} transferred from {old_ward.name if old_ward else 'unknown'} to {new_ward.name}",
    )
    db.session.add(activity)
    db.session.commit()
    flash('Patient transferred successfully.', 'success')
    return redirect(url_for('patients.list_patients'))



@patients_bp.route('/patients')
@login_required
def list_patients():
    patients = Patient.query.all()
    wards = Ward.query.all()
    teams = Team.query.all()
    current_date = datetime.now(UTC).strftime('%Y-%m-%d')
    return render_template('patients/list.html', patients=patients, wards=wards, teams=teams, current_date=current_date)
# Add patient route (admin/staff)
@patients_bp.route('/patients/add', methods=['POST'])
@login_required
@roles_required('admin', 'staff')
def add_patient():
    name = request.form.get('name')
    age = request.form.get('age')
    gender = request.form.get('gender')
    ward_name = request.form.get('ward_name')
    team_id = request.form.get('team_id')
    admission_date = request.form.get('admission_date')
    if not (name and age and gender and ward_name and team_id and admission_date):
        flash('All fields are required.', 'danger')
        return redirect(url_for('patients.list_patients'))
    ward = Ward.query.filter(Ward.name.ilike(ward_name.strip())).first()
    if not ward:
        flash('Ward with that name does not exist.', 'danger')
        return redirect(url_for('patients.list_patients'))
    # Gender validation: only enforce if ward.type is 'male' or 'female'
    if ward.type.lower() in ['male', 'female']:
        if ward.type.lower() != gender.lower():
            flash('Selected ward does not match patient gender.', 'danger')
            return redirect(url_for('patients.list_patients'))
    # Capacity validation
    if ward.available_beds() < 1:
        flash('Selected ward has no available beds.', 'danger')
        return redirect(url_for('patients.list_patients'))
    # Team validation: must have at least one Consultant and one Grade 1/Junior doctor
    import re
    from app.models import Team, Doctor
    team = Team.query.get(int(team_id))
    if not team:
        flash('Selected team does not exist.', 'danger')
        return redirect(url_for('patients.list_patients'))

    # Normalize and check common variants (case/spacing/short forms)
    def is_consultant(grade_str):
        if not grade_str:
            return False
        g = grade_str.strip().lower()
        return bool(re.search(r'consult', g))

    def is_junior(grade_str):
        if not grade_str:
            return False
        g = grade_str.strip().lower()
        # match 'grade 1', 'grade1', 'g1', 'junior', etc.
        return bool(re.search(r'grade\s*1|grade1|\bg1\b|junior', g))

    doctor_count = len(team.doctors or [])
    has_consultant = any(is_consultant(d.grade) for d in team.doctors)
    has_junior = any(is_junior(d.grade) for d in team.doctors)

    if doctor_count == 0:
        flash('Selected team has no doctors; please add doctors to the team first.', 'danger')
        return redirect(url_for('patients.list_patients'))
    # Prepare readable doctor list for diagnostics
    doctor_lines = [f"{d.name} ({(d.grade or 'unknown').strip()})" for d in team.doctors]
    doctor_list_text = '; '.join(doctor_lines) if doctor_lines else 'No doctors'
    if not has_consultant:
        flash(f'Selected team must have at least one Consultant (found {doctor_count} doctors). Doctors: {doctor_list_text}', 'danger')
        return redirect(url_for('patients.list_patients'))
    if not has_junior:
        flash(f'Selected team must have at least one Grade 1 / junior doctor (found {doctor_count} doctors). Doctors: {doctor_list_text}', 'danger')
        return redirect(url_for('patients.list_patients'))
    try:
        admission_date_obj = datetime.strptime(admission_date, '%Y-%m-%d')
    except Exception:
        admission_date_obj = datetime.now(UTC)
    new_patient = Patient(
        name=name,
        age=int(age),
        gender=gender,
        ward_id=ward.id,
        team_id=int(team_id),
        admission_date=admission_date_obj
    )
    db.session.add(new_patient)
    # Update ward occupancy
    ward.current_occupancy = ward.current_occupancy + 1
    db.session.commit()
    # Audit log
    audit_logger.info(f"User '{getattr(current_user, 'username', 'unknown')}' admitted patient '{name}' (ID: {new_patient.id}) to ward '{ward.name}' (ID: {ward.id}) on {admission_date_obj.strftime('%Y-%m-%d')}")
    # Activity log
    activity = ActivityLog(
        user_id=getattr(current_user, 'id', None),
        username=getattr(current_user, 'username', 'unknown'),
        action='Add Patient',
        details=f"{name} admitted to {ward.name}",
    )
    db.session.add(activity)
    db.session.commit()
    flash('Patient added successfully.', 'success')
    return redirect(url_for('patients.list_patients'))


@patients_bp.route('/patients/<int:id>')
@login_required
def patient_details(id):
    patient = Patient.query.get_or_404(id)
    from app.models import Nurse
    nurses = Nurse.query.filter_by(team_id=patient.team_id).all()
    return render_template('patients/detail.html', patient=patient, nurses=nurses)


# Delete patient route (admin/staff)
@patients_bp.route('/patients/<int:id>/delete', methods=['POST'])
@login_required
@roles_required('admin', 'staff')
def delete_patient(id):
    patient = Patient.query.get_or_404(id)
    # Update ward occupancy if patient was assigned to a ward
    try:
        ward = patient.assigned_ward
        if ward and ward.current_occupancy > 0:
            ward.current_occupancy = max(0, ward.current_occupancy - 1)
    except Exception:
        # If anything goes wrong reading the relationship, continue with delete to avoid blocking admin actions
        ward = None
    db.session.delete(patient)
    db.session.commit()
    # Activity log
    activity = ActivityLog(
        user_id=getattr(current_user, 'id', None),
        username=getattr(current_user, 'username', 'unknown'),
        action='Delete Patient',
        details=f"{patient.name} deleted from {ward.name if ward else 'unknown'}",
    )
    db.session.add(activity)
    db.session.commit()
    flash('Patient deleted successfully.', 'success')
    return redirect(url_for('patients.list_patients'))

# Discharge patient route (admin/staff)
@patients_bp.route('/patients/<int:id>/discharge', methods=['POST'])
@login_required
@roles_required('admin', 'staff')
def discharge_patient(id):
    patient = Patient.query.get_or_404(id)
    if patient.discharge_date:
        flash('Patient is already discharged.', 'info')
    else:
        patient.discharge_date = datetime.now(UTC)
        db.session.commit()
        # Audit log
        audit_logger.info(f"User '{getattr(current_user, 'username', 'unknown')}' discharged patient '{patient.name}' (ID: {patient.id}) from ward '{patient.assigned_ward.name if patient.assigned_ward else 'unknown'}' (ID: {patient.assigned_ward.id if patient.assigned_ward else 'unknown'}) on {patient.discharge_date.strftime('%Y-%m-%d %H:%M:%S')}")
        # Activity log
        activity = ActivityLog(
            user_id=patient.id,  # Log as patient, not admin
            username=patient.name,  # Show patient name in activity feed
            action='Discharge Patient',
            details=f"{patient.name} discharged from {patient.assigned_ward.name if patient.assigned_ward else 'unknown'}",
        )
        db.session.add(activity)
        db.session.commit()
        flash('Patient discharged successfully.', 'success')
    return redirect(url_for('patients.list_patients'))