from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Patient, Doctor, TreatmentLog

treatment_bp = Blueprint('treatment', __name__)

@treatment_bp.route('/patients/<int:patient_id>/treat', methods=['POST'])
@login_required
def treat_patient(patient_id):
    patient = db.session.get(Patient, patient_id)
    if not patient:
        from flask import abort
        abort(404)
    doctor_id = request.form.get('doctor_id')
    notes = request.form.get('notes', '')
    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        flash('Doctor not found.', 'danger')
        return redirect(url_for('patients.patient_details', id=patient_id))
    # Only allow doctors from the assigned team
    if doctor.team_id != patient.team_id:
        flash('Doctor is not part of the assigned team for this patient.', 'danger')
        return redirect(url_for('patients.patient_details', id=patient_id))
    medication = request.form.get('medication')
    dosage = request.form.get('dosage')
    nurse_id = request.form.get('nurse_id')
    nurse = None
    if nurse_id:
        from app.models import Nurse
        nurse = db.session.get(Nurse, nurse_id)
    log = TreatmentLog(
        patient_id=patient.id,
        doctor_id=doctor.id,
        notes=notes,
        medication=medication,
        dosage=dosage,
        nurse_id=nurse.id if nurse else None
    )
    db.session.add(log)
    db.session.commit()
    flash('Treatment recorded successfully.', 'success')
    return redirect(url_for('patients.patient_details', id=patient_id))
