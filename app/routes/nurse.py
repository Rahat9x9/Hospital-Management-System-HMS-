from flask import Blueprint, render_template
from flask_login import login_required

nurse_bp = Blueprint('nurse', __name__)


from app.models import Ward, Patient

@nurse_bp.route('/nurse')
@login_required
def dashboard():
    from flask_login import current_user
    if not (current_user.is_authenticated and (current_user.role or '').lower() == 'nurse'):
        from flask import abort
        abort(403)
    wards = Ward.query.all()
    patients = Patient.query.filter(Patient.discharge_date == None).order_by(Patient.admission_date.desc()).all()
    return render_template('nurse/dashboard.html', wards=wards, patients=patients)
