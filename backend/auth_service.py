#!/usr/bin/env python3
"""
Authentication service for multi-user support
Handles user registration, login, and credential encryption
"""

import sqlite3
import os
import jwt
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from flask import Flask, jsonify, request, g, current_app
from functools import wraps
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['DATABASE'] = os.environ.get('DATABASE_PATH', 'users.db')
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev_secret_key_change_in_production')

# Generate or load encryption key for passwords
# Check environment variable first (for production/Railway)
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
if ENCRYPTION_KEY:
    # Environment variable exists, use it (must be base64 encoded)
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()
else:
    # Fall back to file-based key for local development
    ENCRYPTION_KEY_FILE = '.encryption_key'
    if os.path.exists(ENCRYPTION_KEY_FILE):
        with open(ENCRYPTION_KEY_FILE, 'rb') as f:
            ENCRYPTION_KEY = f.read()
    else:
        ENCRYPTION_KEY = Fernet.generate_key()
        try:
            with open(ENCRYPTION_KEY_FILE, 'wb') as f:
                f.write(ENCRYPTION_KEY)
        except (IOError, PermissionError) as e:
            logger.warning(f"Could not write encryption key file: {e}. Using in-memory key.")

fernet = Fernet(ENCRYPTION_KEY)


def get_db():
    """Get database connection"""
    if 'db' not in g:
        # Use current_app to get the app in the current context
        database_path = current_app.config['DATABASE']
        g.db = sqlite3.connect(
            database_path,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize the database schema"""
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            apple_id TEXT NOT NULL,
            apple_password_encrypted TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.commit()


def encrypt_password(password):
    """Encrypt a password using Fernet symmetric encryption"""
    return fernet.encrypt(password.encode()).decode()


def decrypt_password(encrypted_password):
    """Decrypt a password"""
    return fernet.decrypt(encrypted_password.encode()).decode()


def generate_token(user_id):
    """Generate JWT token for user"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token


def verify_token(token):
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None


def require_auth(f):
    """Decorator to require authentication for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401

        try:
            # Expected format: "Bearer <token>"
            token = auth_header.split(' ')[1]
            user_id = verify_token(token)

            if user_id is None:
                return jsonify({"error": "Invalid or expired token"}), 401

            # Store user_id in request context
            g.user_id = user_id
            return f(*args, **kwargs)

        except (IndexError, KeyError):
            return jsonify({"error": "Invalid authorization header format"}), 401

    return decorated_function


def create_user(username, apple_id, apple_password):
    """Create a new user with encrypted credentials"""
    db = get_db()

    # Check if username already exists
    existing_user = db.execute(
        'SELECT id FROM users WHERE username = ?',
        (username,)
    ).fetchone()

    if existing_user:
        return None, "Username already exists"

    # Encrypt password
    encrypted_password = encrypt_password(apple_password)

    # Insert user
    try:
        cursor = db.execute(
            'INSERT INTO users (username, apple_id, apple_password_encrypted) VALUES (?, ?, ?)',
            (username, apple_id, encrypted_password)
        )
        db.commit()
        return cursor.lastrowid, None
    except sqlite3.IntegrityError as e:
        logger.error(f"Database error creating user: {e}")
        return None, "Failed to create user"


def authenticate_user(username, apple_id, apple_password):
    """Authenticate user and return user data if successful"""
    db = get_db()

    user = db.execute(
        'SELECT id, username, apple_id, apple_password_encrypted FROM users WHERE username = ?',
        (username,)
    ).fetchone()

    if not user:
        return None

    # Verify credentials
    stored_apple_id = user['apple_id']
    stored_encrypted_password = user['apple_password_encrypted']

    try:
        decrypted_password = decrypt_password(stored_encrypted_password)
    except Exception as e:
        logger.error(f"Failed to decrypt password: {e}")
        return None

    if apple_id == stored_apple_id and apple_password == decrypted_password:
        return {
            'id': user['id'],
            'username': user['username'],
            'apple_id': user['apple_id']
        }

    return None


def get_user_credentials(user_id):
    """Get decrypted credentials for a user"""
    db = get_db()

    user = db.execute(
        'SELECT apple_id, apple_password_encrypted FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()

    if not user:
        return None

    try:
        decrypted_password = decrypt_password(user['apple_password_encrypted'])
        return {
            'apple_id': user['apple_id'],
            'apple_password': decrypted_password
        }
    except Exception as e:
        logger.error(f"Failed to decrypt credentials: {e}")
        return None


@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json

    username = data.get('username')
    apple_id = data.get('apple_id')
    apple_password = data.get('apple_password')

    if not username or not apple_id or not apple_password:
        return jsonify({"error": "username, apple_id, and apple_password are required"}), 400

    user_id, error = create_user(username, apple_id, apple_password)

    if error:
        return jsonify({"error": error}), 400

    # Generate token
    token = generate_token(user_id)

    return jsonify({
        "success": True,
        "token": token,
        "user_id": user_id
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json

    username = data.get('username')
    apple_id = data.get('apple_id')
    apple_password = data.get('apple_password')

    if not username or not apple_id or not apple_password:
        return jsonify({"error": "username, apple_id, and apple_password are required"}), 400

    user = authenticate_user(username, apple_id, apple_password)

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    # Generate token
    token = generate_token(user['id'])

    return jsonify({
        "success": True,
        "token": token,
        "user_id": user['id']
    }), 200


if __name__ == '__main__':
    with app.app_context():
        init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
