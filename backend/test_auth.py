#!/usr/bin/env python3
"""
Unit tests for multi-user authentication
Following TDD approach
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import jwt
from datetime import datetime, timedelta
from auth_service import (
    app,
    init_db,
    create_user,
    authenticate_user,
    encrypt_password,
    decrypt_password,
    generate_token,
    verify_token
)


class TestUserRegistration(unittest.TestCase):
    """Test cases for user registration"""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['DATABASE'] = ':memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        init_db()

    def tearDown(self):
        self.app_context.pop()

    def test_register_user_success(self):
        """Should register a new user with encrypted credentials"""
        # Act
        response = self.client.post('/api/auth/register',
                                    json={
                                        'username': 'testuser',
                                        'apple_id': 'test@icloud.com',
                                        'apple_password': 'test_password'
                                    },
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 201)
        self.assertTrue(data['success'])
        self.assertIn('token', data)

    def test_register_user_duplicate_username(self):
        """Should reject duplicate username"""
        # Arrange
        self.client.post('/api/auth/register',
                        json={
                            'username': 'testuser',
                            'apple_id': 'test@icloud.com',
                            'apple_password': 'test_password'
                        },
                        content_type='application/json')

        # Act
        response = self.client.post('/api/auth/register',
                                    json={
                                        'username': 'testuser',
                                        'apple_id': 'another@icloud.com',
                                        'apple_password': 'another_password'
                                    },
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)

    def test_register_user_missing_fields(self):
        """Should reject registration with missing fields"""
        # Act
        response = self.client.post('/api/auth/register',
                                    json={'username': 'testuser'},
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)


class TestUserLogin(unittest.TestCase):
    """Test cases for user login"""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['DATABASE'] = ':memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        init_db()
        # Create a test user
        self.client.post('/api/auth/register',
                       json={
                           'username': 'testuser',
                           'apple_id': 'test@icloud.com',
                           'apple_password': 'test_password'
                       },
                       content_type='application/json')

    def tearDown(self):
        self.app_context.pop()

    def test_login_success(self):
        """Should login with valid credentials"""
        # Act
        response = self.client.post('/api/auth/login',
                                    json={
                                        'username': 'testuser',
                                        'apple_id': 'test@icloud.com',
                                        'apple_password': 'test_password'
                                    },
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('token', data)

    def test_login_invalid_credentials(self):
        """Should reject invalid credentials"""
        # Act
        response = self.client.post('/api/auth/login',
                                    json={
                                        'username': 'testuser',
                                        'apple_id': 'test@icloud.com',
                                        'apple_password': 'wrong_password'
                                    },
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', data)

    def test_login_nonexistent_user(self):
        """Should reject login for nonexistent user"""
        # Act
        response = self.client.post('/api/auth/login',
                                    json={
                                        'username': 'nonexistent',
                                        'apple_id': 'test@icloud.com',
                                        'apple_password': 'test_password'
                                    },
                                    content_type='application/json')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', data)


class TestPasswordEncryption(unittest.TestCase):
    """Test cases for password encryption/decryption"""

    def test_encrypt_decrypt_password(self):
        """Should encrypt and decrypt password correctly"""
        # Arrange
        original_password = 'my_secure_password_123'

        # Act
        encrypted = encrypt_password(original_password)
        decrypted = decrypt_password(encrypted)

        # Assert
        self.assertNotEqual(original_password, encrypted)
        self.assertEqual(original_password, decrypted)

    def test_encrypted_password_is_different(self):
        """Should produce different encrypted values each time"""
        # Arrange
        password = 'test_password'

        # Act
        encrypted1 = encrypt_password(password)
        encrypted2 = encrypt_password(password)

        # Assert
        # Note: This depends on using a random IV/salt
        self.assertNotEqual(encrypted1, encrypted2)
        self.assertEqual(password, decrypt_password(encrypted1))
        self.assertEqual(password, decrypt_password(encrypted2))


class TestJWTTokens(unittest.TestCase):
    """Test cases for JWT token generation and verification"""

    def test_generate_and_verify_token(self):
        """Should generate and verify JWT token"""
        # Arrange
        user_id = 123

        # Act
        token = generate_token(user_id)
        verified_user_id = verify_token(token)

        # Assert
        self.assertIsNotNone(token)
        self.assertEqual(user_id, verified_user_id)

    def test_verify_invalid_token(self):
        """Should reject invalid token"""
        # Act
        result = verify_token('invalid.token.here')

        # Assert
        self.assertIsNone(result)

    def test_verify_expired_token(self):
        """Should reject expired token"""
        # Arrange
        user_id = 123
        # Create token that expires immediately
        expired_token = jwt.encode(
            {'user_id': user_id, 'exp': datetime.utcnow() - timedelta(seconds=1)},
            'test_secret',
            algorithm='HS256'
        )

        # Act
        result = verify_token(expired_token)

        # Assert
        self.assertIsNone(result)


# Note: TestProtectedEndpoints will be added after integrating auth_service with icloud_service


if __name__ == '__main__':
    unittest.main()
