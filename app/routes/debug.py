from flask import Blueprint, current_app, render_template_string
from flask_login import login_required, current_user
from app import db
from app.models import Team, Doctor

debug_bp = Blueprint('debug', __name__, url_prefix='/debug')


@debug_bp.route('/teams')
@login_required
def teams_debug():
    # Only allow in debug mode
    if not current_app.debug:
        return "Not available", 404
    # Only allow admins
    if not current_user.is_authenticated or getattr(current_user, 'role', None) != 'admin':
        return "Forbidden", 403

    teams = Team.query.all()
    rows = []
    for t in teams:
        docs = []
        for d in t.doctors:
            docs.append({'id': d.id, 'name': d.name, 'grade': d.grade, 'specialization': d.specialization})
        rows.append({'id': t.id, 'code': t.code, 'name': t.name, 'doctors': docs})

    # Simple HTML
    html = """
    <h1>Teams & Doctors (debug)</h1>
    {% for t in teams %}
      <h2>{{t.code}} - {{t.name}}</h2>
      <ul>
      {% for d in t.doctors %}
        <li>{{d.name}} — {{d.grade}} — {{d.specialization}}</li>
      {% endfor %}
      </ul>
    {% endfor %}
    """
    return render_template_string(html, teams=rows)


@debug_bp.route('/teams.json')
@login_required
def teams_json():
    if not current_app.debug:
        return {"error": "Not available"}, 404
    if not current_user.is_authenticated or getattr(current_user, 'role', None) != 'admin':
        return {"error": "Forbidden"}, 403
    teams = Team.query.all()
    out = {}
    for t in teams:
        out[t.id] = {
            'code': t.code,
            'name': t.name,
            'doctors': [{'id': d.id, 'name': d.name, 'grade': d.grade, 'specialization': d.specialization} for d in t.doctors]
        }
    return out


@debug_bp.route('/teams/<int:team_id>/seed_doctors', methods=['POST', 'GET'])
@login_required
def seed_team_doctors(team_id):
    """Create a minimal set of doctors for a team (Consultant + Grade 1) — debug only."""
    if not current_app.debug:
        return {"error": "Not available"}, 404
    if not current_user.is_authenticated or getattr(current_user, 'role', None) != 'admin':
        return {"error": "Forbidden"}, 403
    team = Team.query.get(team_id)
    if not team:
        return {"error": "Team not found"}, 404
    # If team already has doctors, report and do nothing
    if team.doctors and len(team.doctors) > 0:
        return {"message": f"Team {team.id} already has {len(team.doctors)} doctors."}
    # Create consultant and grade 1
    c1 = Doctor(name=f'Auto Consultant {team.code}', grade='Consultant', specialization=team.specialization or 'General', team_id=team.id)
    j1 = Doctor(name=f'Auto Junior {team.code}', grade='Grade 1', specialization=team.specialization or 'General', team_id=team.id)
    db.session.add_all([c1, j1])
    db.session.commit()
    return {"message": f"Added 2 doctors to team {team.id}", "doctors": [{"id": c1.id, "name": c1.name, "grade": c1.grade}, {"id": j1.id, "name": j1.name, "grade": j1.grade}]}
