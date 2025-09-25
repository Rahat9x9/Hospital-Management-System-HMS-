from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.models import User, Doctor, Nurse, Technician, Team, db
from app.utils import roles_required

# ----------------- Blueprint -----------------
staff_bp = Blueprint('staff', __name__)

# ----------------- Staff List -----------------
@staff_bp.route('/staff')
@login_required
@roles_required('admin')
def staff_list():
    users = User.query.all()
    doctors = Doctor.query.all()
    technicians = Technician.query.all()
    nurses = Nurse.query.all()
    teams = Team.query.all()

    # Map nurses to their user accounts
    nurse_users = [
        {
            'id': n.id,
            'name': n.name,
            'grade': n.grade,
            'username': (User.query.get(n.user_id).username if n.user_id else ''),
            'email': (User.query.get(n.user_id).email if n.user_id else '')
        }
        for n in nurses
    ]

    return render_template(
        'staff/list.html',
        users=users,
        doctors=doctors,
        nurses=nurse_users,
        technicians=technicians,
        teams=teams
    )

# ----------------- Doctor Routes -----------------
@staff_bp.route('/staff/doctor/add', methods=['POST'])
@login_required
@roles_required('admin')
def add_doctor():
    name = request.form.get('name')
    specialization = request.form.get('specialization')
    grade = request.form.get('grade')
    team_id = request.form.get('team_id')
    user_id = request.form.get('user_id') or None

    if not (name and specialization and grade and team_id):
        flash('All required fields must be filled!', 'danger')
        return redirect(url_for('staff.staff_list'))

    # Check if user_id is already assigned
    if user_id and (Doctor.query.filter_by(user_id=user_id).first() or
                    Nurse.query.filter_by(user_id=user_id).first() or
                    Technician.query.filter_by(user_id=user_id).first()):
        flash('Selected user is already assigned to another staff member!', 'danger')
        return redirect(url_for('staff.staff_list'))

    # Optional: Check duplicate doctor name in same team
    if Doctor.query.filter_by(name=name, team_id=team_id).first():
        flash('Doctor with this name already exists in the selected team!', 'danger')
        return redirect(url_for('staff.staff_list'))

    try:
        new_doctor = Doctor(
            name=name,
            specialization=specialization,
            grade=grade,
            team_id=int(team_id),
            user_id=int(user_id) if user_id else None
        )
        db.session.add(new_doctor)
        db.session.commit()
        flash('Doctor added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding doctor: {str(e)}', 'danger')

    return redirect(url_for('staff.staff_list'))

@staff_bp.route('/staff/doctor/<int:id>/delete', methods=['POST'])
@login_required
@roles_required('admin')
def delete_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    try:
        db.session.delete(doctor)
        db.session.commit()
        flash('Doctor deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting doctor: {str(e)}', 'danger')
    return redirect(url_for('staff.staff_list'))

# ----------------- Nurse Routes -----------------
@staff_bp.route('/staff/nurse/add', methods=['POST'])
@login_required
@roles_required('admin')
def add_nurse():
    name = request.form.get('name')
    grade = request.form.get('grade')
    user_id = request.form.get('user_id') or None

    if not (name and grade):
        flash('Name and Grade are required!', 'danger')
        return redirect(url_for('staff.staff_list'))

    # Check if user_id is already assigned
    if user_id and (Nurse.query.filter_by(user_id=user_id).first() or
                    Doctor.query.filter_by(user_id=user_id).first() or
                    Technician.query.filter_by(user_id=user_id).first()):
        flash('Selected user is already assigned to another staff member!', 'danger')
        return redirect(url_for('staff.staff_list'))

    try:
        new_nurse = Nurse(name=name, grade=grade, user_id=int(user_id) if user_id else None)
        db.session.add(new_nurse)
        db.session.commit()
        flash('Nurse added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding nurse: {str(e)}', 'danger')

    return redirect(url_for('staff.staff_list'))

@staff_bp.route('/staff/nurse/<int:id>/delete', methods=['POST'])
@login_required
@roles_required('admin')
def delete_nurse(id):
    nurse = Nurse.query.get_or_404(id)
    try:
        db.session.delete(nurse)
        db.session.commit()
        flash('Nurse deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting nurse: {str(e)}', 'danger')
    return redirect(url_for('staff.staff_list'))

# ----------------- Technician Routes -----------------
@staff_bp.route('/staff/technician/add', methods=['POST'])
@login_required
@roles_required('admin')
def add_technician():
    name = request.form.get('name')
    specialization = request.form.get('specialization')
    user_id = request.form.get('user_id') or None

    if not (name and specialization):
        flash('All fields are required.', 'danger')
        return redirect(url_for('staff.staff_list'))

    # Check if user_id is already assigned
    if user_id and (Technician.query.filter_by(user_id=user_id).first() or
                    Nurse.query.filter_by(user_id=user_id).first() or
                    Doctor.query.filter_by(user_id=user_id).first()):
        flash('Selected user is already assigned to another staff member!', 'danger')
        return redirect(url_for('staff.staff_list'))

    try:
        new_tech = Technician(name=name, specialization=specialization, user_id=int(user_id) if user_id else None)
        db.session.add(new_tech)
        db.session.commit()
        flash('Technician added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding technician: {str(e)}', 'danger')

    return redirect(url_for('staff.staff_list'))

@staff_bp.route('/staff/technician/<int:id>/delete', methods=['POST'])
@login_required
@roles_required('admin')
def delete_technician(id):
    tech = Technician.query.get_or_404(id)
    try:
        db.session.delete(tech)
        db.session.commit()
        flash('Technician deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting technician: {str(e)}', 'danger')
    return redirect(url_for('staff.staff_list'))
