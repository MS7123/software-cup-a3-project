"""Test helper: authenticated FastAPI TestClient fixture."""

import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.db.session import get_engine
from app.main import create_app


class AuthenticatedTestCase(unittest.TestCase):
    """Base for test cases that need an authenticated API client.

    Every test method gets a fresh temporary SQLite database, registers a
    test user, and provides ``self.client`` (a ``TestClient``) pre-configured
    with a Bearer token.
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_url = f"sqlite:///{Path(self.temp_dir.name) / 'auth-test.sqlite3'}"
        self._previous_env = {
            "APP_DATABASE_URL": os.environ.get("APP_DATABASE_URL"),
            "AUTH_SECRET_KEY": os.environ.get("AUTH_SECRET_KEY"),
        }
        os.environ["APP_DATABASE_URL"] = self.database_url
        os.environ["AUTH_SECRET_KEY"] = "test-secret-key"

        # Clear engine cache so create_app() picks up the new database URL
        get_engine.cache_clear()

        self.client = TestClient(create_app())

        # Register a test user and capture the token
        resp = self.client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "testpass123"},
        )
        token_data = resp.json()
        self.token = token_data["access_token"]
        self.user_id = token_data["user_id"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self) -> None:
        self.client.close()
        # Restore previous environment
        for key, value in self._previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        # Clean up engine cache for this database URL
        get_engine().dispose()
        get_engine(self.database_url).dispose()
        get_engine.cache_clear()
        self.temp_dir.cleanup()
