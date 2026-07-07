import unittest
from utils.cooldown import CooldownManager

class TestCooldown(unittest.TestCase):
    def test_cooldown_manager_flow(self):
        """Verifies cooldown tracking, remaining calculations, and reset options."""
        manager = CooldownManager()
        user_id = 9999
        command = "start"
        
        # Initially, no cooldown
        self.assertEqual(manager.get_remaining_cooldown(user_id, command, 60.0), 0.0)
        
        # Trigger command
        manager.update_cooldown(user_id, command)
        
        # Remaining cooldown should be close to 60.0
        rem = manager.get_remaining_cooldown(user_id, command, 60.0)
        self.assertTrue(50.0 <= rem <= 60.0)
        
        # Reset cooldown
        manager.reset_cooldown(user_id, command)
        self.assertEqual(manager.get_remaining_cooldown(user_id, command, 60.0), 0.0)

if __name__ == "__main__":
    unittest.main()
