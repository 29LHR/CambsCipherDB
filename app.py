from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import func
import os
from dotenv import load_dotenv
import functools


load_dotenv()
# Enforce API key protection for all endpoints. Set DB_API_KEY in the environment
# and clients must send header `X-API-KEY` with this value.
EXPECTED_API_KEY = os.getenv('DB_API_KEY')
if not EXPECTED_API_KEY:
    raise RuntimeError("DB_API_KEY must be set for the DB service")

def require_api_key(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        key = request.headers.get('X-API-KEY') or request.args.get('api_key')
        if key != EXPECTED_API_KEY:
            return jsonify({'error': 'unauthorized'}), 401
        return fn(*args, **kwargs)
    return wrapper

app = Flask(__name__)
CORS(app)

database_url = os.getenv('DATABASE_URL') or 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=True)
    birthdate = db.Column(db.String(10), nullable=True)
    firstName = db.Column(db.String(100), nullable=True)
    lastName = db.Column(db.String(100), nullable=True)
    school = db.Column(db.String(250), nullable=True)
    points = db.Column(db.Integer, default=0, nullable=False)

class Challenges(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    published = db.Column(db.Boolean, default=False, nullable=False)
    ciphertext = db.Column(db.Text, nullable=True)
    plaintext = db.Column(db.Text, nullable=True)
    tips = db.Column(db.Text, nullable=True)
    title = db.Column(db.String(250), nullable=True)
    points_reward = db.Column(db.Integer, default=10, nullable=False)
    release_time = db.Column(db.DateTime, nullable=True)
    closing_time = db.Column(db.DateTime, nullable=True)

    def get_status(self):
        if not self.published:
            return 'unpublished'
        now = datetime.now()
        if self.release_time and now < self.release_time:
            return 'upcoming'
        if self.closing_time and now > self.closing_time:
            return 'closed'
        return 'active'

class CompletedChallenges(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.now)
    time_taken_seconds = db.Column(db.Integer, nullable=True)
    points_earned = db.Column(db.Integer, nullable=True)
    __table_args__ = (db.UniqueConstraint('user_id', 'challenge_id', name='unique_user_challenge'),)

class ChallengeAttempts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.now)
    __table_args__ = (db.UniqueConstraint('user_id', 'challenge_id', name='unique_user_challenge_attempt'),)

def calculate_points(base_points, time_seconds):
    if time_seconds < 600:
        multiplier = 2.0
    elif time_seconds < 3600:
        multiplier = 1.5
    elif time_seconds < 18000:
        multiplier = 1.25
    elif time_seconds < 36000:
        multiplier = 1.1
    elif time_seconds < 108000:
        multiplier = 1.05
    else:
        multiplier = 1.0
    return int(base_points * multiplier)

with app.app_context():
    db.create_all()

@app.route('/api/challenges')
@require_api_key
def api_list_challenges():
    rows = Challenges.query.order_by(Challenges.id).all()
    out = []
    for r in rows:
        out.append({
            'id': r.id,
            'title': r.title,
            'published': r.published,
            'status': r.get_status(),
            'points_reward': r.points_reward,
        })
    return jsonify(out)

@app.route('/api/challenges/<int:id>')
@require_api_key
def api_get_challenge(id):
    r = Challenges.query.get_or_404(id)
    return jsonify({
        'id': r.id,
        'title': r.title,
        'published': r.published,
        'ciphertext': r.ciphertext,
        'plaintext': r.plaintext,
        'tips': r.tips,
        'points_reward': r.points_reward,
        'release_time': r.release_time.isoformat() if r.release_time else None,
        'closing_time': r.closing_time.isoformat() if r.closing_time else None,
        'status': r.get_status(),
    })

@app.route('/api/challenges/<int:id>/attempt', methods=['POST'])
@require_api_key
def api_start_attempt(id):
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        abort(400)
    existing = ChallengeAttempts.query.filter_by(user_id=user_id, challenge_id=id).first()
    if existing:
        return jsonify({'started_at': existing.started_at.isoformat()})
    attempt = ChallengeAttempts(user_id=user_id, challenge_id=id)
    db.session.add(attempt)
    db.session.commit()
    return jsonify({'started_at': attempt.started_at.isoformat()})

@app.route('/api/challenges/<int:id>/submit', methods=['POST'])
@require_api_key
def api_submit(id):
    data = request.get_json() or {}
    user_id = data.get('user_id')
    answer = data.get('answer', '')
    if not user_id:
        abort(400)
    ch = Challenges.query.get_or_404(id)
    # normalize
    ans_norm = ''.join(c.lower() for c in answer if c.isalpha())
    correct = ''.join(c.lower() for c in (ch.plaintext or '') if c.isalpha())
    if ans_norm != correct:
        return jsonify({'ok': False, 'reason': 'incorrect'}), 200

    # determine time taken
    attempt = ChallengeAttempts.query.filter_by(user_id=user_id, challenge_id=id).first()
    if ch.release_time:
        time_taken = (datetime.now() - ch.release_time).total_seconds()
    elif attempt:
        time_taken = (datetime.now() - attempt.started_at).total_seconds()
    else:
        time_taken = 108000
    time_taken_seconds = int(time_taken)
    points = calculate_points(ch.points_reward, time_taken_seconds)

    # record completion if not already
    existing = CompletedChallenges.query.filter_by(user_id=user_id, challenge_id=id).first()
    if existing:
        return jsonify({'ok': False, 'reason': 'already_completed'}), 200

    comp = CompletedChallenges(user_id=user_id, challenge_id=id, time_taken_seconds=time_taken_seconds, points_earned=points)
    db.session.add(comp)
    user = Users.query.get(user_id)
    if user:
        user.points = (user.points or 0) + points
    db.session.commit()
    return jsonify({'ok': True, 'points': points, 'time_seconds': time_taken_seconds})


@app.route('/api/users/<int:id>/completed')
@require_api_key
def api_user_completed(id):
    rows = CompletedChallenges.query.filter_by(user_id=id).all()
    return jsonify([{'challenge_id': r.challenge_id, 'completed_at': r.completed_at.isoformat() if r.completed_at else None, 'points': r.points_earned} for r in rows])


@app.route('/api/users/<int:id>/password', methods=['PUT'])
@require_api_key
def api_update_password(id):
    data = request.get_json() or {}
    new_password = data.get('password')
    if not new_password:
        abort(400)
    u = Users.query.get_or_404(id)
    u.password = generate_password_hash(new_password, method='pbkdf2:sha256')
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/users/by-username/<username>')
@require_api_key
def api_get_user_by_username(username):
    u = Users.query.filter(func.lower(Users.username) == username.lower()).first()
    if not u:
        abort(404)
    return jsonify({
        'id': u.id,
        'username': u.username,
        'password': u.password,
        'email': u.email,
        'firstName': u.firstName,
        'lastName': u.lastName,
        'birthdate': u.birthdate,
        'school': u.school,
        'points': u.points,
    })


@app.route('/api/users/by-email/<email>')
@require_api_key
def api_get_user_by_email(email):
    u = Users.query.filter(func.lower(Users.email) == email.lower()).first()
    if not u:
        abort(404)
    return jsonify({
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'firstName': u.firstName,
        'lastName': u.lastName,
        'birthdate': u.birthdate,
        'school': u.school,
        'points': u.points,
    })

@app.route('/api/users/<int:id>')
@require_api_key
def api_get_user(id):
    u = Users.query.get_or_404(id)
    return jsonify({
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'firstName': u.firstName,
        'lastName': u.lastName,
        'birthdate': u.birthdate,
        'school': u.school,
        'points': u.points,
    })

@app.route('/api/users', methods=['POST'])
@require_api_key
def api_create_user():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    if not username or not password:
        abort(400)
    if Users.query.filter_by(username=username).first():
        return jsonify({'ok': False, 'reason': 'username_taken'}), 200
    if email and Users.query.filter_by(email=email).first():
        return jsonify({'ok': False, 'reason': 'email_taken'}), 200
    hashed = generate_password_hash(password, method='pbkdf2:sha256')
    u = Users(username=username, password=hashed, email=email, birthdate=data.get('birthdate'), firstName=data.get('firstName'), lastName=data.get('lastName'), school=data.get('school'))
    db.session.add(u)
    db.session.commit()
    return jsonify({'ok': True, 'id': u.id})

@app.route('/api/users/<int:id>', methods=['PUT'])
@require_api_key
def api_update_user(id):
    data = request.get_json() or {}
    u = Users.query.get_or_404(id)
    for f in ('firstName','lastName','email','birthdate','school'):
        if f in data:
            setattr(u, f, data[f])
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/users/<int:id>', methods=['DELETE'])
@require_api_key
def api_delete_user(id):
    u = Users.query.get_or_404(id)
    CompletedChallenges.query.filter_by(user_id=id).delete()
    db.session.delete(u)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/leaderboard')
@require_api_key
def api_leaderboard():
    users = Users.query.order_by(Users.points.desc()).all()
    out = []
    for u in users:
        out.append({'id': u.id, 'username': u.username, 'school': u.school or 'N/A', 'points': u.points})
    return jsonify(out)


if __name__ == '__main__':
    port = int(os.getenv('PORT', '5600'))
    app.run(host='127.0.0.1', port=port, debug=True)
