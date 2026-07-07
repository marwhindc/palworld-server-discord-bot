import os
import unittest
from unittest.mock import patch
from config import Config

class TestConfig(unittest.TestCase):
    @patch.dict(os.environ, {
        "DISCORD_TOKEN": "test_token",
        "GCP_PROJECT_ID": "test_project",
        "GCP_ZONE": "us-central1-a",
        "INSTANCE_NAME": "test_instance",
        "ALLOWED_ROLE": "test_role",
        "ALLOWED_CHANNEL_ID": "12345",
        "PALWORLD_REST_URL": "http://localhost:8212/",
        "PALWORLD_REST_USERNAME": "admin",
        "PALWORLD_REST_PASSWORD": "password123",
        "START_COOLDOWN": "120",
        "STOP_COOLDOWN": "240",
    })
    def test_load_config_success(self):
        config = Config.load_from_env()
        self.assertEqual(config.DISCORD_TOKEN, "test_token")
        self.assertEqual(config.GCP_PROJECT_ID, "test_project")
        self.assertEqual(config.GCP_ZONE, "us-central1-a")
        self.assertEqual(config.INSTANCE_NAME, "test_instance")
        self.assertEqual(config.ALLOWED_ROLE, "test_role")
        self.assertEqual(config.ALLOWED_CHANNEL_ID, 12345)
        # Strips trailing slash
        self.assertEqual(config.PALWORLD_REST_URL, "http://localhost:8212")
        self.assertEqual(config.PALWORLD_REST_USERNAME, "admin")
        self.assertEqual(config.PALWORLD_REST_PASSWORD, "password123")
        self.assertEqual(config.START_COOLDOWN, 120)
        self.assertEqual(config.STOP_COOLDOWN, 240)

    @patch.dict(os.environ, {})
    def test_load_config_missing_vars(self):
        with self.assertRaises(ValueError) as ctx:
            Config.load_from_env()
        self.assertIn("Missing required environment variables", str(ctx.exception))

    @patch.dict(os.environ, {
        "DISCORD_TOKEN": "test_token",
        "GCP_PROJECT_ID": "test_project",
        "GCP_ZONE": "us-central1-a",
        "INSTANCE_NAME": "test_instance",
        "ALLOWED_ROLE": "test_role",
        "ALLOWED_CHANNEL_ID": "invalid_integer",
        "PALWORLD_REST_URL": "http://localhost:8212/",
        "PALWORLD_REST_USERNAME": "admin",
        "PALWORLD_REST_PASSWORD": "password123",
    })
    def test_load_config_invalid_channel_id(self):
        with self.assertRaises(ValueError) as ctx:
            Config.load_from_env()
        self.assertIn("ALLOWED_CHANNEL_ID must be a valid integer", str(ctx.exception))

if __name__ == "__main__":
    unittest.main()
