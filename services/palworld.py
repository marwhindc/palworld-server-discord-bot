import asyncio
import time
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse, urlunparse
import aiohttp
from utils.logger import bot_logger

class PalworldService:
    """Manages REST API interactions with the Palworld Dedicated Server."""

    def __init__(self, rest_url: str, username: str, password: str):
        self.rest_url = rest_url
        self.auth = aiohttp.BasicAuth(username, password)

    def get_url(self, ip: Optional[str] = None) -> str:
        """Returns the REST URL, dynamically replacing the host with the current VM IP if available."""
        if not ip:
            return self.rest_url
        try:
            parsed = urlparse(self.rest_url)
            netloc = f"{ip}:{parsed.port}" if parsed.port else ip
            return urlunparse(parsed._replace(netloc=netloc))
        except Exception as e:
            bot_logger.error(f"Failed to parse or override REST URL: {e}")
            return self.rest_url

    async def is_server_online(self, ip: Optional[str] = None) -> bool:
        """Checks if the Palworld REST API is online and responding."""
        base_url = self.get_url(ip)
        url = f"{base_url}/v1/api/info"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, auth=self.auth, timeout=5) as response:
                    return response.status == 200
        except Exception:
            # Silent fail for periodic status checks
            return False

    async def get_players(self, ip: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves the list of currently online players."""
        base_url = self.get_url(ip)
        url = f"{base_url}/v1/api/players"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, auth=self.auth, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("players", [])
                    else:
                        bot_logger.error(f"Palworld API returned status {response.status} for players query.")
                        return []
        except Exception as e:
            bot_logger.error(f"Failed to fetch players list from Palworld at {url}: {e}", exc_info=True)
            raise

    async def get_player_count(self, ip: Optional[str] = None) -> int:
        """Helper to get current online player count directly."""
        try:
            players = await self.get_players(ip)
            return len(players)
        except Exception:
            return 0

    async def get_metrics(self, ip: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves server performance metrics from the API."""
        base_url = self.get_url(ip)
        url = f"{base_url}/v1/api/metrics"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, auth=self.auth, timeout=5) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception:
            return None

    async def shutdown(self, waittime: int = 10, message: str = "Server shutting down via Discord.", ip: Optional[str] = None) -> bool:
        """Sends a POST request to shutdown the Palworld server gracefully."""
        base_url = self.get_url(ip)
        url = f"{base_url}/v1/api/shutdown"
        payload = {
            "waittime": waittime,
            "message": message
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, auth=self.auth, json=payload, timeout=5) as response:
                    if response.status == 200:
                        bot_logger.info(f"Graceful server shutdown triggered: {payload}")
                        return True
                    else:
                        bot_logger.error(f"Shutdown POST request returned status {response.status}")
                        return False
        except Exception as e:
            bot_logger.error(f"Failed to execute shutdown API request: {e}", exc_info=True)
            return False

    async def wait_until_ready(self, timeout: int = 300, poll_interval: int = 5, ip: Optional[str] = None) -> bool:
        """Polls the API until the Palworld server is fully online and ready."""
        start_time = time.time()
        bot_logger.info("Waiting for Palworld Dedicated Server REST API to be ready...")
        while time.time() - start_time < timeout:
            if await self.is_server_online(ip):
                duration = time.time() - start_time
                bot_logger.info(f"Palworld Dedicated Server REST API is online. Elapsed: {duration:.1f}s")
                return True
            await asyncio.sleep(poll_interval)
        bot_logger.error("Timeout waiting for Palworld Dedicated Server REST API to become ready.")
        return False
