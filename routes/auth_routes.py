from flask import Blueprint, request, jsonify
from models.user import User
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

auth_bp = Blueprint('auth', __name__)

# Register a new user
@auth_bp.route('/register', methods=['POST'])
def register():
    print("Register endpoint hit")
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"msg": "Username and password required"}), 400

    if User.objects(username=data['username']).first():
        return jsonify({"msg": "Username already exists"}), 400

    hashed_pw = generate_password_hash(data['password']).decode('utf-8')
    user = User(username=data['username'], password=hashed_pw)
    user.save()
    return jsonify({"msg": "User registered successfully"}), 201

# Login an existing user
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"msg": "Username and password required"}), 400

    user = User.objects(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        token = create_access_token(identity=str(user.id))
        return jsonify({"token": token}), 200

    return jsonify({"msg": "Invalid credentials"}), 401

@auth_bp.route('/ping', methods=['GET'])
def ping():
    return jsonify({"msg": "Auth route is working!"})
