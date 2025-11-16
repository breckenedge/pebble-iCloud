#!/usr/bin/env python3
"""
Helper script to generate secure secret keys for production deployment
"""

import secrets
from cryptography.fernet import Fernet


def generate_jwt_secret():
    """Generate a secure JWT secret key"""
    return secrets.token_urlsafe(64)


def generate_encryption_key():
    """Generate a Fernet encryption key"""
    return Fernet.generate_key().decode()


if __name__ == '__main__':
    print("=== Production Secret Keys ===\n")
    print("Copy these to your Railway/Heroku environment variables:\n")
    print(f"JWT_SECRET_KEY={generate_jwt_secret()}\n")
    print(f"ENCRYPTION_KEY={generate_encryption_key()}\n")
    print("⚠️  IMPORTANT: Keep these secure and never commit them to git!")
