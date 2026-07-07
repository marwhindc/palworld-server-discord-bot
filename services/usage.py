import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from utils.logger import bot_logger
from config import Config

class UsageService:
    """Manages VM running time statistics and cost calculations."""

    def __init__(self, db_path: str = "data/usage.json"):
        self.db_path = db_path
        self._data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """Loads usage logs from local file, resetting them if a new month has started."""
        if not os.path.exists(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            default_data = {
                "current_month": self._get_current_month_str(),
                "total_seconds": 0.0,
                "last_start_time": None
            }
            self._save_data_to_file(default_data)
            return default_data
        
        try:
            with open(self.db_path, "r") as f:
                data = json.load(f)
            
            # Check for month rollover
            current_month = self._get_current_month_str()
            if data.get("current_month") != current_month:
                bot_logger.info(
                    f"Month rollover detected from {data.get('current_month')} to {current_month}. "
                    "Resetting monthly running hour counters."
                )
                data = {
                    "current_month": current_month,
                    "total_seconds": 0.0,
                    "last_start_time": None
                }
                self._save_data_to_file(data)
            return data
        except Exception as e:
            bot_logger.error(f"Error loading usage data: {e}", exc_info=True)
            return {
                "current_month": self._get_current_month_str(),
                "total_seconds": 0.0,
                "last_start_time": None
            }

    def _save_data_to_file(self, data: Dict[str, Any]):
        """Writes current data state to file."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            bot_logger.error(f"Error saving usage data: {e}", exc_info=True)

    def _get_current_month_str(self) -> str:
        """Returns UTC date formatted as YYYY-MM."""
        return datetime.utcnow().strftime("%Y-%m")

    def record_start(self):
        """Records VM startup session start time."""
        self._data = self._load_data()
        if self._data["last_start_time"] is None:
            self._data["last_start_time"] = time.time()
            self._save_data_to_file(self._data)
            bot_logger.info("Recorded VM startup time for billing calculations.")

    def record_stop(self):
        """Records VM shutdown session stop time, adding duration to the total."""
        self._data = self._load_data()
        start_time = self._data["last_start_time"]
        if start_time is not None:
            elapsed = time.time() - start_time
            if elapsed > 0:
                self._data["total_seconds"] += elapsed
            self._data["last_start_time"] = None
            self._save_data_to_file(self._data)
            bot_logger.info(
                f"Recorded VM shutdown. Added {elapsed:.1f}s to runtime. "
                f"Total this month: {self._data['total_seconds']:.1f}s."
            )

    def update_active_session(self):
        """Calculates runtime since the last check and flushes it to the database.

        Prevents data loss in case of system power failure or bot crashes mid-session.
        """
        self._data = self._load_data()
        start_time = self._data["last_start_time"]
        if start_time is not None:
            now = time.time()
            elapsed = now - start_time
            if elapsed > 0:
                self._data["total_seconds"] += elapsed
                self._data["last_start_time"] = now  # Shift start pointer forward
                self._save_data_to_file(self._data)
                bot_logger.debug(f"Periodically flushed active session time. Added {elapsed:.1f}s.")

    def get_total_hours_this_month(self) -> float:
        """Calculates total running hours this month, including active runtime."""
        self._data = self._load_data()
        total_sec = self._data["total_seconds"]
        start_time = self._data["last_start_time"]
        if start_time is not None:
            total_sec += (time.time() - start_time)
        return total_sec / 3600.0

    def calculate_estimated_cost(self, config: Config) -> Dict[str, float]:
        """Returns details on running hours, storage cost, compute cost, and total spent."""
        hours = self.get_total_hours_this_month()
        compute_cost = hours * config.VM_HOURLY_RATE
        storage_cost = config.DISK_SIZE_GB * config.DISK_GB_MONTHLY_RATE
        total_cost = compute_cost + storage_cost
        
        return {
            "hours": hours,
            "compute_cost": compute_cost,
            "storage_cost": storage_cost,
            "total_cost": total_cost
        }
