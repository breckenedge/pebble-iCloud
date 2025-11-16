#!/usr/bin/env python3
"""
Multi-user iCloud Reminders Service for Pebble Watch Integration
Production-ready multi-tenant deployment
Following TDD approach
"""

import os
import logging
import re
from flask import Flask, jsonify, g, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
from pyicloud import PyiCloudService

# Import auth functions
from auth_service import (
    init_db,
    require_auth,
    get_user_credentials,
    close_db,
    create_user,
    authenticate_user,
    generate_token
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate required environment variables in production
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
if FLASK_ENV == 'production':
    required_vars = ['JWT_SECRET_KEY', 'ENCRYPTION_KEY']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.info("Production mode: All required environment variables present")

app = Flask(__name__)
CORS(app, origins=['https://*', 'http://localhost:*'] if FLASK_ENV == 'production' else '*')

# Configuration
app.config['DATABASE'] = os.environ.get('DATABASE_PATH', 'users.db')
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev_secret_key_change_in_production')
app.config['PROPAGATE_EXCEPTIONS'] = True

# Production settings
if FLASK_ENV == 'production':
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    logger.info("Running in PRODUCTION mode")
else:
    logger.warning("Running in DEVELOPMENT mode")

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Setup teardown handlers
app.teardown_appcontext(close_db)

# Initialize database when module is loaded (for gunicorn)
with app.app_context():
    init_db()


# Input validation helpers
def validate_email(email):
    """Validate email format for Apple ID"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username):
    """Validate username (alphanumeric, underscore, hyphen, 3-30 chars)"""
    pattern = r'^[a-zA-Z0-9_-]{3,30}$'
    return re.match(pattern, username) is not None


# Auth endpoints
@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    """Register a new user"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        username = data.get('username')
        apple_id = data.get('apple_id')
        apple_password = data.get('apple_password')

        if not username or not apple_id or not apple_password:
            return jsonify({"error": "username, apple_id, and apple_password are required"}), 400

        # Validate username format
        if not validate_username(username):
            return jsonify({"error": "Username must be 3-30 characters (alphanumeric, underscore, hyphen only)"}), 400

        # Validate Apple ID is email format
        if not validate_email(apple_id):
            return jsonify({"error": "Apple ID must be a valid email address"}), 400

        # Validate password length
        if len(apple_password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400

        user_id, error = create_user(username, apple_id, apple_password)

        if error:
            return jsonify({"error": error}), 400

        # Generate token
        token = generate_token(user_id)
        logger.info(f"New user registered: {username}")

        return jsonify({
            "success": True,
            "token": token,
            "user_id": user_id
        }), 201

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Login user (rate limited to prevent brute force)"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        username = data.get('username')
        apple_id = data.get('apple_id')
        apple_password = data.get('apple_password')

        if not username or not apple_id or not apple_password:
            return jsonify({"error": "username, apple_id, and apple_password are required"}), 400

        user = authenticate_user(username, apple_id, apple_password)

        if not user:
            logger.warning(f"Failed login attempt for username: {username}")
            return jsonify({"error": "Invalid credentials"}), 401

        # Generate token
        token = generate_token(user['id'])
        logger.info(f"User logged in: {username}")

        return jsonify({
            "success": True,
            "token": token,
            "user_id": user['id']
        }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


def get_icloud_service_for_user(user_id):
    """Get or create iCloud service instance for a specific user"""
    # Get user credentials from database
    credentials = get_user_credentials(user_id)

    if not credentials:
        raise ValueError("User credentials not found")

    apple_id = credentials['apple_id']
    apple_password = credentials['apple_password']

    try:
        icloud = PyiCloudService(apple_id, apple_password)

        # Check if 2FA is required
        if icloud.requires_2fa:
            logger.warning(f"2FA required for user {user_id}")
            # In a production system, you'd need a way to handle this
            # For now, we'll raise an error
            raise Exception("Two-factor authentication required. Please authenticate via the web interface.")

        return icloud
    except Exception as e:
        logger.error(f"Failed to create iCloud service for user {user_id}: {e}")
        raise


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": FLASK_ENV,
        "version": "2.0.0"
    })


@app.route('/api/reminders/lists', methods=['GET'])
@require_auth
def get_reminder_lists():
    """Get all reminder lists for authenticated user"""
    try:
        user_id = g.user_id
        service = get_icloud_service_for_user(user_id)
        lists = []

        for collection in service.reminders.collections:
            lists.append({
                "id": collection.guid,
                "title": collection.title,
                "color": getattr(collection, 'color', None)
            })

        return jsonify({"lists": lists})
    except Exception as e:
        logger.error(f"Error fetching reminder lists: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/reminders/list/<list_id>', methods=['GET'])
@require_auth
def get_reminders(list_id):
    """Get reminders from a specific list for authenticated user"""
    try:
        user_id = g.user_id
        service = get_icloud_service_for_user(user_id)

        # Find the collection
        collection = None
        for col in service.reminders.collections:
            if col.guid == list_id:
                collection = col
                break

        if not collection:
            return jsonify({"error": "List not found"}), 404

        reminders = []
        for reminder in collection:
            reminders.append({
                "id": reminder.get('guid'),
                "title": reminder.get('title'),
                "description": reminder.get('description', ''),
                "completed": reminder.get('completed', False),
                "due_date": reminder.get('dueDate'),
                "priority": reminder.get('priority', 0)
            })

        return jsonify({"reminders": reminders})
    except Exception as e:
        logger.error(f"Error fetching reminders: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/reminders', methods=['POST'])
@require_auth
def create_reminder():
    """Create a new reminder for authenticated user"""
    try:
        user_id = g.user_id
        service = get_icloud_service_for_user(user_id)
        data = request.json

        list_id = data.get('list_id')
        title = data.get('title')
        description = data.get('description', '')

        if not list_id or not title:
            return jsonify({"error": "list_id and title are required"}), 400

        # Find the collection
        collection = None
        for col in service.reminders.collections:
            if col.guid == list_id:
                collection = col
                break

        if not collection:
            return jsonify({"error": "List not found"}), 404

        # Create reminder
        reminder = collection.add_reminder(title, description=description)

        return jsonify({
            "success": True,
            "reminder": {
                "id": reminder.get('guid'),
                "title": reminder.get('title'),
                "description": reminder.get('description', '')
            }
        }), 201
    except Exception as e:
        logger.error(f"Error creating reminder: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/reminders/<reminder_id>/complete', methods=['POST'])
@require_auth
def complete_reminder(reminder_id):
    """Mark a reminder as completed for authenticated user"""
    try:
        user_id = g.user_id
        service = get_icloud_service_for_user(user_id)
        data = request.json
        list_id = data.get('list_id')

        if not list_id:
            return jsonify({"error": "list_id is required"}), 400

        # Find the collection
        collection = None
        for col in service.reminders.collections:
            if col.guid == list_id:
                collection = col
                break

        if not collection:
            return jsonify({"error": "List not found"}), 404

        # Find and complete the reminder
        for reminder in collection:
            if reminder.get('guid') == reminder_id:
                reminder['completed'] = True
                collection.save()
                return jsonify({"success": True})

        return jsonify({"error": "Reminder not found"}), 404
    except Exception as e:
        logger.error(f"Error completing reminder: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    with app.app_context():
        init_db()
    port = int(os.environ.get('PORT', 5000))
    debug_mode = FLASK_ENV != 'production'

    if FLASK_ENV == 'production':
        logger.warning("Running with built-in Flask server in production is not recommended.")
        logger.warning("Use a production WSGI server like Gunicorn: gunicorn app:app")

    app.run(host='0.0.0.0', port=port, debug=debug_mode)
