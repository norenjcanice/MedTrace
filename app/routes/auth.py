from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from app.models import User
from app import db

bp = Blueprint('auth', __name__)

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized', 'message': 'Please log in first'}), 401
            if session.get('role') not in roles:
                return jsonify({'error': 'Forbidden', 'message': 'You do not have permission to access this resource'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid input', 'message': 'No JSON data provided'}), 400

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if not all([name, email, password, role]):
        return jsonify({'error': 'Missing fields', 'message': 'Name, email, password, and role are required'}), 400
        
    valid_roles = ['manufacturer', 'distributor', 'pharmacy', 'user']
    if role not in valid_roles:
        return jsonify({'error': 'Invalid role', 'message': f'Role must be one of {valid_roles}'}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'User exists', 'message': 'A user with this email already exists'}), 409

    hashed_password = generate_password_hash(password)
    
    new_user = User(
        name=name,
        email=email,
        password=hashed_password,
        role=role
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'user': {
            'id': new_user.id,
            'name': new_user.name,
            'email': new_user.email,
            'role': new_user.role
        }
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid input', 'message': 'No JSON data provided'}), 400

    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'error': 'Missing fields', 'message': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        session['role'] = user.role
        
        return jsonify({
            'message': 'Logged in successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role
            }
        }), 200
        
    return jsonify({'error': 'Invalid credentials', 'message': 'Incorrect email or password'}), 401

@bp.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200
