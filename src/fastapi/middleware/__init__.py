"""Expose middleware classes for the FastAPI shim."""

from .cors import CORSMiddleware

__all__ = ["CORSMiddleware"]
