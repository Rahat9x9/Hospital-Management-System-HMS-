from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Ward, db
from app.utils import roles_required
wards_bp = Blueprint('wards', __name__)

@wards_bp.route('/wards/<int:id>/edit', methods=['POST'])
@login_required
@roles_required('admin', 'staff')
def edit_ward(id):
    ward = db.session.get(Ward, id)
    if not ward:
        from flask import abort
        abort(404)
    name = request.form.get('name')
    type_ = request.form.get('type')
    capacity = request.form.get('capacity')
    if not (name and type_ and capacity):
        flash('All fields are required.', 'danger')
        return redirect(url_for('wards.list_wards'))
    try:
        capacity = int(capacity)
    except Exception:
        flash('Capacity must be a number.', 'danger')
        return redirect(url_for('wards.list_wards'))
    ward.name = name
    ward.type = type_
    ward.capacity = capacity
    db.session.commit()
    flash('Ward updated successfully.', 'success')
    return redirect(url_for('wards.list_wards'))

@wards_bp.route('/wards/<int:id>/delete', methods=['POST'])
@login_required
@roles_required('admin', 'staff')
def delete_ward(id):
    ward = db.session.get(Ward, id)
    if not ward:
        from flask import abort
        abort(404)
    db.session.delete(ward)
    db.session.commit()
    flash('Ward deleted successfully.', 'success')
    return redirect(url_for('wards.list_wards'))



@wards_bp.route('/wards')
@login_required
def list_wards():
    wards = Ward.query.all()
    # Filter full wards in Python for template use
    full_wards = [w for w in wards if w.current_occupancy >= w.capacity]
    return render_template('wards/list.html', wards=wards, full_wards=full_wards, current_user=current_user)

# Add ward route (admin/staff)
@wards_bp.route('/wards/add', methods=['POST'])
@login_required
@roles_required('admin', 'staff')
def add_ward():
    name = request.form.get('name')
    type_ = request.form.get('type')
    capacity = request.form.get('capacity')
    if not (name and type_ and capacity):
        flash('All fields are required.', 'danger')
        return redirect(url_for('wards.list_wards'))
    try:
        capacity = int(capacity)
    except Exception:
        flash('Capacity must be a number.', 'danger')
        return redirect(url_for('wards.list_wards'))
    new_ward = Ward(name=name, type=type_, capacity=capacity, current_occupancy=0)
    db.session.add(new_ward)
    db.session.commit()
    flash('Ward added successfully.', 'success')
    return redirect(url_for('wards.list_wards'))

@wards_bp.route('/wards/<int:id>')
@login_required
def ward_details(id):
    ward = db.session.get(Ward, id)
    if not ward:
        from flask import abort
        abort(404)
    return render_template('wards/detail.html', ward=ward)