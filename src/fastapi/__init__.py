"""Minimal FastAPI-compatible shim used for offline testing."""

from .applications import FastAPI
from .dependencies import Depends
from .exceptions import HTTPException
from .params import Form, Header
from .routing import APIRouter
from .testclient import TestClient

from . import status
from .middleware.cors import CORSMiddleware

__all__ = [
    "FastAPI",
    "APIRouter",
    "Depends",
    "HTTPException",
    "TestClient",
    "Form",
    "Header",
    "status",
    "CORSMiddleware",
]
