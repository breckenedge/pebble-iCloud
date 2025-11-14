#!/usr/bin/env python3
"""
iCloud Reminders Service for Pebble Watch Integration
Handles authentication and API communication with iCloud Reminders
Focus: Reminders only (TDD approach)
"""

from pyicloud import PyiCloudService
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global iCloud service instance
icloud = None


def get_icloud_service():
    """Initialize or return existing iCloud service instance"""
    global icloud
    if icloud is None:
        apple_id = os.environ.get('APPLE_ID')
        password = os.environ.get('APPLE_PASSWORD')

        if not apple_id or not password:
            raise ValueError("APPLE_ID and APPLE_PASSWORD environment variables must be set")

        icloud = PyiCloudService(apple_id, password)

        # Handle 2FA if required
        if icloud.requires_2fa:
            logger.info("Two-factor authentication required")
            # In production, you'd handle this more gracefully
            code = input("Enter the code you received: ")
            result = icloud.validate_2fa_code(code)
            if not result:
                logger.error("Failed to verify 2FA code")
                raise Exception("Invalid 2FA code")

    return icloud


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route('/api/reminders/lists', methods=['GET'])
def get_reminder_lists():
    """Get all reminder lists"""
    try:
        service = get_icloud_service()
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
def get_reminders(list_id):
    """Get reminders from a specific list"""
    try:
        service = get_icloud_service()

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
def create_reminder():
    """Create a new reminder"""
    try:
        service = get_icloud_service()
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
def complete_reminder(reminder_id):
    """Mark a reminder as completed"""
    try:
        service = get_icloud_service()
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
