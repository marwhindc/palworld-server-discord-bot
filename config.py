import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

@dataclass(frozen=True)
class Config:
    DISCORD_TOKEN: str
    GCP_PROJECT_ID: str
    GCP_ZONE: str
    INSTANCE_NAME: str
    ALLOWED_ROLE: str
    ALLOWED_CHANNEL_ID: int
    PALWORLD_REST_URL: str
    PALWORLD_REST_USERNAME: str
    PALWORLD_REST_PASSWORD: str
    START_COOLDOWN: int
    STOP_COOLDOWN: int

    @classmethod
    def load_from_env(cls) -> "Config":
        """Loads and validates configuration from environment variables.

        Raises:
            ValueError: If any required configuration variables are missing or invalid.
        """
        required = [
            "DISCORD_TOKEN",
            "GCP_PROJECT_ID",
            "GCP_ZONE",
            "INSTANCE_NAME",
            "ALLOWED_ROLE",
            "ALLOWED_CHANNEL_ID",
            "PALWORLD_REST_URL",
            "PALWORLD_REST_USERNAME",
            "PALWORLD_REST_PASSWORD",
        ]
        
        missing = [var for var in required if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        try:
            channel_id = int(os.getenv("ALLOWED_CHANNEL_ID", "0"))
        except ValueError as e:
            raise ValueError("ALLOWED_CHANNEL_ID must be a valid integer") from e

        try:
            start_cooldown = int(os.getenv("START_COOLDOWN", "300"))
        except ValueError:
            start_cooldown = 300

        try:
            stop_cooldown = int(os.getenv("STOP_COOLDOWN", "300"))
        except ValueError:
            stop_cooldown = 300

        # Standardize rest URL by stripping trailing slash
        rest_url = os.getenv("PALWORLD_REST_URL", "").rstrip("/")

        return cls(
            DISCORD_TOKEN=os.getenv("DISCORD_TOKEN", ""),
            GCP_PROJECT_ID=os.getenv("GCP_PROJECT_ID", ""),
            GCP_ZONE=os.getenv("GCP_ZONE", ""),
            INSTANCE_NAME=os.getenv("INSTANCE_NAME", ""),
            ALLOWED_ROLE=os.getenv("ALLOWED_ROLE", ""),
            ALLOWED_CHANNEL_ID=channel_id,
            PALWORLD_REST_URL=rest_url,
            PALWORLD_REST_USERNAME=os.getenv("PALWORLD_REST_USERNAME", ""),
            PALWORLD_REST_PASSWORD=os.getenv("PALWORLD_REST_PASSWORD", ""),
            START_COOLDOWN=start_cooldown,
            STOP_COOLDOWN=stop_cooldown,
        )
