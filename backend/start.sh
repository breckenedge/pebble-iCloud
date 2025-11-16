#!/bin/bash
# Start script for Railway deployment
# This ensures the PORT environment variable is properly expanded

exec gunicorn app:app --workers 4 --timeout 60 --bind "0.0.0.0:${PORT}"
