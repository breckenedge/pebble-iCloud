#!/usr/bin/env python3
"""
Database configuration utility
Supports both SQLite (development) and PostgreSQL (production)
"""

import os
import logging

logger = logging.getLogger(__name__)


def get_database_url():
    """
    Get database URL based on environment.

    Returns:
        str: Database connection string
    """
    # Check for DATABASE_URL (provided by Railway, Heroku, etc.)
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # Fix postgres:// to postgresql:// for SQLAlchemy compatibility
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
            logger.info("Converted postgres:// to postgresql:// in DATABASE_URL")

        logger.info("Using PostgreSQL database from DATABASE_URL")
        return database_url

    # Fallback to SQLite for development
    database_path = os.environ.get('DATABASE_PATH', 'users.db')
    logger.info(f"Using SQLite database: {database_path}")
    return f'sqlite:///{database_path}'


def is_postgres():
    """Check if we're using PostgreSQL"""
    return os.environ.get('DATABASE_URL') is not None


def get_db_connection():
    """
    Get a raw database connection for direct SQL operations.

    Returns:
        Connection object (sqlite3 or psycopg2)
    """
    if is_postgres():
        import psycopg2
        from urllib.parse import urlparse

        database_url = get_database_url()
        result = urlparse(database_url)

        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        logger.info("Connected to PostgreSQL")
        return conn
    else:
        import sqlite3
        database_path = os.environ.get('DATABASE_PATH', 'users.db')
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        logger.info(f"Connected to SQLite: {database_path}")
        return conn


def init_database_schema(conn):
    """
    Initialize database schema (works for both SQLite and PostgreSQL)

    Args:
        conn: Database connection
    """
    cursor = conn.cursor()

    if is_postgres():
        # PostgreSQL schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(30) UNIQUE NOT NULL,
                apple_id VARCHAR(255) NOT NULL,
                apple_password_encrypted TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("PostgreSQL schema created/verified")
    else:
        # SQLite schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                apple_id TEXT NOT NULL,
                apple_password_encrypted TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("SQLite schema created/verified")

    conn.commit()


if __name__ == '__main__':
    """Test database configuration"""
    logging.basicConfig(level=logging.INFO)

    print(f"Database URL: {get_database_url()}")
    print(f"Using PostgreSQL: {is_postgres()}")

    try:
        conn = get_db_connection()
        init_database_schema(conn)
        print("Database schema initialized successfully!")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
