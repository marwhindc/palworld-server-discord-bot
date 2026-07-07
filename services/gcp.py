import asyncio
import time
from typing import Optional
from google.cloud import compute_v1
from utils.logger import bot_logger

class GCPService:
    """Manages GCP Compute Engine instances asynchronously."""

    def __init__(self, project_id: str, zone: str, instance_name: str):
        self.project_id = project_id
        self.zone = zone
        self.instance_name = instance_name
        # The client initialization itself does not perform I/O
        self.client = compute_v1.InstancesClient()

    async def get_instance_status(self) -> str:
        """Retrieves the current status of the GCE instance (e.g.

        'RUNNING', 'TERMINATED').
        """
        def _get_status():
            instance = self.client.get(
                project=self.project_id,
                zone=self.zone,
                instance=self.instance_name
            )
            return instance.status

        try:
            return await asyncio.to_thread(_get_status)
        except Exception as e:
            bot_logger.error(f"GCP API failure in get_instance_status: {e}", exc_info=True)
            raise

    async def start_instance(self):
        """Triggers the VM instance startup."""
        def _start():
            return self.client.start(
                project=self.project_id,
                zone=self.zone,
                instance=self.instance_name
            )

        bot_logger.info(f"Initiating startup for VM instance: {self.instance_name}")
        try:
            await asyncio.to_thread(_start)
        except Exception as e:
            bot_logger.error(f"GCP API failure in start_instance: {e}", exc_info=True)
            raise

    async def stop_instance(self):
        """Triggers the VM instance shutdown."""
        def _stop():
            return self.client.stop(
                project=self.project_id,
                zone=self.zone,
                instance=self.instance_name
            )

        bot_logger.info(f"Initiating shutdown for VM instance: {self.instance_name}")
        try:
            await asyncio.to_thread(_stop)
        except Exception as e:
            bot_logger.error(f"GCP API failure in stop_instance: {e}", exc_info=True)
            raise

    async def get_external_ip(self) -> Optional[str]:
        """Retrieves the external NAT IP of the instance."""
        def _get_ip():
            instance = self.client.get(
                project=self.project_id,
                zone=self.zone,
                instance=self.instance_name
            )
            for interface in instance.network_interfaces:
                for config in interface.access_configs:
                    if config.nat_i_p:
                        return config.nat_i_p
            return None

        try:
            return await asyncio.to_thread(_get_ip)
        except Exception as e:
            bot_logger.error(f"GCP API failure in get_external_ip: {e}", exc_info=True)
            raise

    async def wait_until_running(self, timeout: int = 300, poll_interval: int = 5) -> bool:
        """Polls GCE until the instance is RUNNING or the timeout is reached."""
        start_time = time.time()
        bot_logger.info(f"Waiting for VM {self.instance_name} to enter RUNNING state...")
        while time.time() - start_time < timeout:
            try:
                status = await self.get_instance_status()
                bot_logger.debug(f"VM Status: {status}")
                if status == "RUNNING":
                    duration = time.time() - start_time
                    bot_logger.info(f"VM {self.instance_name} is RUNNING. Elapsed: {duration:.1f}s")
                    return True
            except Exception:
                # Keep trying in case of temporary API blips
                bot_logger.warning("Temporary status retrieval failure, retrying...")
            await asyncio.sleep(poll_interval)
        bot_logger.error(f"Timeout waiting for VM {self.instance_name} to enter RUNNING state.")
        return False

    async def wait_until_stopped(self, timeout: int = 300, poll_interval: int = 5) -> bool:
        """Polls GCE until the instance is TERMINATED or the timeout is reached."""
        start_time = time.time()
        bot_logger.info(f"Waiting for VM {self.instance_name} to enter TERMINATED state...")
        while time.time() - start_time < timeout:
            try:
                status = await self.get_instance_status()
                bot_logger.debug(f"VM Status: {status}")
                if status == "TERMINATED":
                    duration = time.time() - start_time
                    bot_logger.info(f"VM {self.instance_name} is TERMINATED. Elapsed: {duration:.1f}s")
                    return True
            except Exception:
                # Keep trying in case of temporary API blips
                bot_logger.warning("Temporary status retrieval failure, retrying...")
            await asyncio.sleep(poll_interval)
        bot_logger.error(f"Timeout waiting for VM {self.instance_name} to enter TERMINATED state.")
        return False
