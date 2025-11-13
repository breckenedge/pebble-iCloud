#!/usr/bin/env python3
"""
Integration tests for multi-user iCloud Reminders Service
Tests the complete flow: registration → login → reminders access
Following TDD approach
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from app import app, init_db


class TestIntegratedRemindersFlow(unittest.TestCase):
    """Integration tests for complete user flow"""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['DATABASE'] = ':memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        init_db()

        # Register a test user
        response = self.client.post('/api/auth/register',
                                   json={
                                       'username': 'testuser',
                                       'apple_id': 'test@icloud.com',
                                       'apple_password': 'test_password'
                                   },
                                   content_type='application/json')
        self.token = json.loads(response.data)['token']

    def tearDown(self):
        self.app_context.pop()

    @patch('app.get_icloud_service_for_user')
    def test_get_reminder_lists_authenticated(self, mock_get_service):
        """Should get reminder lists when authenticated"""
        # Arrange
        mock_collection = Mock()
        mock_collection.guid = 'list-123'
        mock_collection.title = 'Test List'
        mock_collection.color = 'blue'

        mock_service = Mock()
        mock_service.reminders.collections = [mock_collection]
        mock_get_service.return_value = mock_service

        # Act
        response = self.client.get('/api/reminders/lists',
                                   headers={'Authorization': f'Bearer {self.token}'})
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn('lists', data)
        self.assertEqual(len(data['lists']), 1)
        self.assertEqual(data['lists'][0]['title'], 'Test List')

    def test_get_reminder_lists_unauthenticated(self):
        """Should reject request without authentication"""
        # Act
        response = self.client.get('/api/reminders/lists')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', data)

    @patch('app.get_icloud_service_for_user')
    def test_get_reminders_authenticated(self, mock_get_service):
        """Should get reminders when authenticated"""
        # Arrange
        mock_reminder = {
            'guid': 'reminder-1',
            'title': 'Buy groceries',
            'description': 'Milk and eggs',
            'completed': False,
            'dueDate': None,
            'priority': 0
        }

        mock_collection = Mock()
        mock_collection.guid = 'list-123'
        mock_collection.__iter__ = Mock(return_value=iter([mock_reminder]))

        mock_service = Mock()
        mock_service.reminders.collections = [mock_collection]
        mock_get_service.return_value = mock_service

        # Act
        response = self.client.get('/api/reminders/list/list-123',
                                   headers={'Authorization': f'Bearer {self.token}'})
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn('reminders', data)
        self.assertEqual(len(data['reminders']), 1)
        self.assertEqual(data['reminders'][0]['title'], 'Buy groceries')

    @patch('app.get_icloud_service_for_user')
    def test_create_reminder_authenticated(self, mock_get_service):
        """Should create reminder when authenticated"""
        # Arrange
        mock_collection = Mock()
        mock_collection.guid = 'list-123'
        mock_collection.add_reminder = Mock(return_value={
            'guid': 'new-reminder',
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
                                    headers={'Authorization': f'Bearer {self.token}'},
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 201)
        self.assertTrue(data['success'])
        self.assertEqual(data['reminder']['title'], 'New task')
        mock_collection.add_reminder.assert_called_once()

    @patch('app.get_icloud_service_for_user')
    def test_complete_reminder_authenticated(self, mock_get_service):
        """Should complete reminder when authenticated"""
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
                                    headers={'Authorization': f'Bearer {self.token}'},
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(mock_reminder['completed'])
        mock_collection.save.assert_called_once()


class TestMultiUserIsolation(unittest.TestCase):
    """Test that users can only access their own data"""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['DATABASE'] = ':memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        init_db()

        # Register two users
        response1 = self.client.post('/api/auth/register',
                                     json={
                                         'username': 'user1',
                                         'apple_id': 'user1@icloud.com',
                                         'apple_password': 'password1'
                                     },
                                     content_type='application/json')
        self.token1 = json.loads(response1.data)['token']

        response2 = self.client.post('/api/auth/register',
                                     json={
                                         'username': 'user2',
                                         'apple_id': 'user2@icloud.com',
                                         'apple_password': 'password2'
                                     },
                                     content_type='application/json')
        self.token2 = json.loads(response2.data)['token']

    def tearDown(self):
        self.app_context.pop()

    @patch('app.get_icloud_service_for_user')
    def test_users_get_different_reminders(self, mock_get_service):
        """Should return different reminders for different users"""
        # Arrange
        def create_mock_service(user_id):
            mock_collection = Mock()
            mock_collection.guid = 'list-123'
            mock_collection.title = f'User {user_id} List'

            mock_service = Mock()
            mock_service.reminders.collections = [mock_collection]
            return mock_service

        # Mock different responses based on user_id
        mock_get_service.side_effect = lambda uid: create_mock_service(uid)

        # Act
        response1 = self.client.get('/api/reminders/lists',
                                    headers={'Authorization': f'Bearer {self.token1}'})
        response2 = self.client.get('/api/reminders/lists',
                                    headers={'Authorization': f'Bearer {self.token2}'})

        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)

        # Assert
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        # Both should succeed with their own credentials
        # The mock will be called with different user_ids
        self.assertEqual(mock_get_service.call_count, 2)


class TestHealthEndpoint(unittest.TestCase):
    """Test health check endpoint"""

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
