"""Vercel entry point for the Flask application.

Kept under api/ so it does not shadow the app/ Python package.
"""
from app import create_app

app = create_app()
