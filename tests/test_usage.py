import os
import time
import unittest
from unittest.mock import MagicMock, patch
from config import Config
from services.usage import UsageService

class TestUsage(unittest.TestCase):
    def setUp(self):
        # Use a temporary test db path to avoid dirtying actual logs
        self.db_path = "data/test_usage.json"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
        self.config = MagicMock(spec=Config)
        self.config.VM_HOURLY_RATE = 0.10
        self.config.DISK_SIZE_GB = 100
        self.config.DISK_GB_MONTHLY_RATE = 0.05

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        # Clean up empty data folder if empty
        try:
            os.rmdir("data")
        except OSError:
            pass

    def test_initialization(self):
        """Verifies database defaults are written correctly on init."""
        service = UsageService(db_path=self.db_path)
        self.assertTrue(os.path.exists(self.db_path))
        self.assertEqual(service._data["total_seconds"], 0.0)
        self.assertIsNone(service._data["last_start_time"])

    @patch("time.time")
    def test_record_start_and_stop(self, mock_time):
        """Verifies recording starts, stops, and accumulates session lengths."""
        service = UsageService(db_path=self.db_path)
        
        # Start at timestamp 1000
        mock_time.return_value = 1000.0
        service.record_start()
        self.assertEqual(service._data["last_start_time"], 1000.0)
        
        # Stop at timestamp 2800 (1800 seconds / 0.5 hours later)
        mock_time.return_value = 2800.0
        service.record_stop()
        
        self.assertIsNone(service._data["last_start_time"])
        self.assertEqual(service._data["total_seconds"], 1800.0)
        self.assertEqual(service.get_total_hours_this_month(), 0.5)

    @patch("time.time")
    def test_update_active_session(self, mock_time):
        """Verifies periodically flushing active session increments database timer."""
        service = UsageService(db_path=self.db_path)
        
        # Start at 1000
        mock_time.return_value = 1000.0
        service.record_start()
        
        # Flush at 1600 (600s elapsed)
        mock_time.return_value = 1600.0
        service.update_active_session()
        
        self.assertEqual(service._data["total_seconds"], 600.0)
        self.assertEqual(service._data["last_start_time"], 1600.0)

    @patch("time.time")
    def test_calculate_estimated_cost(self, mock_time):
        """Verifies correct calculation of compute and storage spent."""
        service = UsageService(db_path=self.db_path)
        
        # Start at 1000, stop at 37000 (36000s / 10 hours elapsed)
        mock_time.return_value = 1000.0
        service.record_start()
        mock_time.return_value = 37000.0
        service.record_stop()
        
        costs = service.calculate_estimated_cost(self.config)
        self.assertEqual(costs["hours"], 10.0)
        # Compute cost: 10 hrs * $0.10/hr = $1.00
        self.assertEqual(costs["compute_cost"], 1.00)
        # Storage cost: 100 GB * $0.05/GB = $5.00
        self.assertEqual(costs["storage_cost"], 5.00)
        # Total cost: $6.00
        self.assertEqual(costs["total_cost"], 6.00)

if __name__ == "__main__":
    unittest.main()
