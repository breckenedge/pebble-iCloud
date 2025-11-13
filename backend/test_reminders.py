#!/usr/bin/env python3
"""
Unit tests for iCloud Reminders API
Following TDD approach
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from icloud_service import app, get_icloud_service


class TestReminderListsEndpoint(unittest.TestCase):
    """Test cases for GET /api/reminders/lists"""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('icloud_service.get_icloud_service')
    def test_get_reminder_lists_success(self, mock_get_service):
        """Should return list of reminder collections"""
        # Arrange
        mock_collection1 = Mock()
        mock_collection1.guid = 'list-123'
        mock_collection1.title = 'Work'
        mock_collection1.color = 'blue'

        mock_collection2 = Mock()
        mock_collection2.guid = 'list-456'
        mock_collection2.title = 'Personal'
        mock_collection2.color = 'red'

        mock_service = Mock()
        mock_service.reminders.collections = [mock_collection1, mock_collection2]
        mock_get_service.return_value = mock_service

        # Act
        response = self.client.get('/api/reminders/lists')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn('lists', data)
        self.assertEqual(len(data['lists']), 2)
        self.assertEqual(data['lists'][0]['title'], 'Work')
        self.assertEqual(data['lists'][1]['title'], 'Personal')

    @patch('icloud_service.get_icloud_service')
    def test_get_reminder_lists_empty(self, mock_get_service):
        """Should handle empty reminder lists"""
        # Arrange
        mock_service = Mock()
        mock_service.reminders.collections = []
        mock_get_service.return_value = mock_service

        # Act
        response = self.client.get('/api/reminders/lists')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['lists']), 0)

    @patch('icloud_service.get_icloud_service')
    def test_get_reminder_lists_error(self, mock_get_service):
        """Should handle errors gracefully"""
        # Arrange
        mock_get_service.side_effect = Exception("iCloud connection failed")

        # Act
        response = self.client.get('/api/reminders/lists')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', data)


class TestGetRemindersEndpoint(unittest.TestCase):
    """Test cases for GET /api/reminders/list/<list_id>"""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('icloud_service.get_icloud_service')
    def test_get_reminders_success(self, mock_get_service):
        """Should return reminders from a specific list"""
        # Arrange
        mock_collection = Mock()
        mock_collection.guid = 'list-123'
        mock_collection.__iter__ = Mock(return_value=iter([
            {
                'guid': 'reminder-1',
                'title': 'Buy groceries',
                'description': 'Milk, eggs, bread',
                'completed': False,
                'dueDate': None,
                'priority': 0
            },
            {
                'guid': 'reminder-2',
                'title': 'Call dentist',
                'description': '',
                'completed': True,
                'dueDate': '2025-11-15',
                'priority': 1
            }
        ]))

        mock_service = Mock()
        mock_service.reminders.collections = [mock_collection]
        mock_get_service.return_value = mock_service

        # Act
        response = self.client.get('/api/reminders/list/list-123')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn('reminders', data)
        self.assertEqual(len(data['reminders']), 2)
        self.assertEqual(data['reminders'][0]['title'], 'Buy groceries')
        self.assertFalse(data['reminders'][0]['completed'])
        self.assertTrue(data['reminders'][1]['completed'])

    @patch('icloud_service.get_icloud_service')
    def test_get_reminders_list_not_found(self, mock_get_service):
        """Should return 404 for non-existent list"""
        # Arrange
        mock_service = Mock()
        mock_service.reminders.collections = []
        mock_get_service.return_value = mock_service

        # Act
        response = self.client.get('/api/reminders/list/nonexistent-list')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', data)


class TestCreateReminderEndpoint(unittest.TestCase):
    """Test cases for POST /api/reminders"""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('icloud_service.get_icloud_service')
    def test_create_reminder_success(self, mock_get_service):
        """Should create a new reminder"""
        # Arrange
        mock_collection = Mock()
        mock_collection.guid = 'list-123'
        mock_collection.add_reminder = Mock(return_value={
            'guid': 'new-reminder-id',
            'title': 'New task',
            'description': 'Task description'
        })

        mock_service = Mock()
        mock_service.reminders.collections = [mock_collection]
        mock_get_service.return_value = mock_service

        # Act
        response = self.client.post('/api/reminders',
                                    json={
                                        'list_id': 'list-123',
                                        'title': 'New task',
                                        'description': 'Task description'
                                    },
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 201)
        self.assertTrue(data['success'])
        self.assertEqual(data['reminder']['title'], 'New task')
        mock_collection.add_reminder.assert_called_once_with(
            'New task',
            description='Task description'
        )

    @patch('icloud_service.get_icloud_service')
    def test_create_reminder_missing_title(self, mock_get_service):
        """Should reject request with missing title"""
        # Act
        response = self.client.post('/api/reminders',
                                    json={'list_id': 'list-123'},
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)

    @patch('icloud_service.get_icloud_service')
    def test_create_reminder_missing_list_id(self, mock_get_service):
        """Should reject request with missing list_id"""
        # Act
        response = self.client.post('/api/reminders',
                                    json={'title': 'New task'},
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)

    @patch('icloud_service.get_icloud_service')
    def test_create_reminder_list_not_found(self, mock_get_service):
        """Should return 404 for non-existent list"""
        # Arrange
        mock_service = Mock()
        mock_service.reminders.collections = []
        mock_get_service.return_value = mock_service

        # Act
        response = self.client.post('/api/reminders',
                                    json={
                                        'list_id': 'nonexistent',
                                        'title': 'New task'
                                    },
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', data)


class TestCompleteReminderEndpoint(unittest.TestCase):
    """Test cases for POST /api/reminders/<reminder_id>/complete"""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('icloud_service.get_icloud_service')
    def test_complete_reminder_success(self, mock_get_service):
        """Should mark reminder as completed"""
        # Arrange
        mock_reminder = {'guid': 'reminder-1', 'completed': False}
        mock_collection = Mock()
        mock_collection.guid = 'list-123'
        mock_collection.__iter__ = Mock(return_value=iter([mock_reminder]))
        mock_collection.save = Mock()

        mock_service = Mock()
        mock_service.reminders.collections = [mock_collection]
        mock_get_service.return_value = mock_service

        # Act
        response = self.client.post('/api/reminders/reminder-1/complete',
                                    json={'list_id': 'list-123'},
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(mock_reminder['completed'])
        mock_collection.save.assert_called_once()

    @patch('icloud_service.get_icloud_service')
    def test_complete_reminder_missing_list_id(self, mock_get_service):
        """Should reject request with missing list_id"""
        # Act
        response = self.client.post('/api/reminders/reminder-1/complete',
                                    json={},
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)

    @patch('icloud_service.get_icloud_service')
    def test_complete_reminder_not_found(self, mock_get_service):
        """Should return 404 for non-existent reminder"""
        # Arrange
        mock_collection = Mock()
        mock_collection.guid = 'list-123'
        mock_collection.__iter__ = Mock(return_value=iter([]))

        mock_service = Mock()
        mock_service.reminders.collections = [mock_collection]
        mock_get_service.return_value = mock_service

        # Act
        response = self.client.post('/api/reminders/nonexistent/complete',
                                    json={'list_id': 'list-123'},
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', data)


class TestHealthEndpoint(unittest.TestCase):
    """Test cases for GET /health"""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_health_check(self):
        """Should return healthy status"""
        # Act
        response = self.client.get('/health')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)


if __name__ == '__main__':
    unittest.main()
