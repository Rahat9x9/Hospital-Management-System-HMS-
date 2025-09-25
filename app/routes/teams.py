from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Team, db
from app.utils import roles_required
teams_bp = Blueprint('teams', __name__)

@teams_bp.route('/teams/<int:id>/edit', methods=['POST'])
@login_required
@roles_required('admin', 'staff')
def edit_team(id):
    team = db.session.get(Team, id)
    if not team:
        from flask import abort
        abort(404)
    code = request.form.get('code')
    name = request.form.get('name')
    specialization = request.form.get('specialization')
    if not (code and name and specialization):
        flash('All fields are required.', 'danger')
        return redirect(url_for('teams.list_teams'))
    team.code = code
    team.name = name
    team.specialization = specialization
    db.session.flush()
    junior_doctors = [d for d in team.doctors if d.grade and (('grade 1' in d.grade.lower()) or ('junior' in d.grade.lower()) or ('g1' in d.grade.lower()))]
    if not junior_doctors:
        db.session.rollback()
        flash('Each team must have at least one Grade-1/junior doctor.', 'danger')
        return redirect(url_for('teams.list_teams'))
    db.session.commit()
    flash('Team updated successfully.', 'success')
    return redirect(url_for('teams.list_teams'))

@teams_bp.route('/teams/<int:id>/delete', methods=['POST'])
@login_required
@roles_required('admin', 'staff')
def delete_team(id):
    team = db.session.get(Team, id)
    if not team:
        from flask import abort
        abort(404)
    db.session.delete(team)
    db.session.commit()
    flash('Team deleted successfully.', 'success')
    return redirect(url_for('teams.list_teams'))



@teams_bp.route('/teams')
@login_required
def list_teams():
    teams = Team.query.all()
    return render_template('teams/list.html', teams=teams, current_user=current_user)

# Add team route (admin/staff)
@teams_bp.route('/teams/add', methods=['POST'])
@login_required
@roles_required('admin', 'staff')
def add_team():
    code = request.form.get('code')
    name = request.form.get('name')
    specialization = request.form.get('specialization')
    if not (code and name and specialization):
        flash('All fields are required.', 'danger')
        return redirect(url_for('teams.list_teams'))
    new_team = Team(code=code, name=name, specialization=specialization)
    db.session.add(new_team)
    db.session.flush()  # get new_team.id
    junior_doctors = [d for d in new_team.doctors if d.grade and (('grade 1' in d.grade.lower()) or ('junior' in d.grade.lower()) or ('g1' in d.grade.lower()))]
    if not junior_doctors:
        db.session.rollback()
        flash('Each team must have at least one Grade-1/junior doctor.', 'danger')
        return redirect(url_for('teams.list_teams'))
    db.session.commit()
    flash('Team added successfully.', 'success')
    return redirect(url_for('teams.list_teams'))

@teams_bp.route('/teams/<int:id>')
@login_required
def team_details(id):
    team = db.session.get(Team, id)
    if not team:
        from flask import abort
        abort(404)
    return render_template('teams/detail.html', team=team)