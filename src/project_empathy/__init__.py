"""Project Empathy SaaS platform for AI restaurant receptionists."""

from .bootstrap import create_schema, seed_demo_data
from .main import create_app

__all__ = ["create_app", "create_schema", "seed_demo_data"]
