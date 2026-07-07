import time
from typing import Dict, Tuple

class CooldownManager:
    """Manages command execution cooldowns dynamically using custom durations."""
    
    def __init__(self):
        # Stores (user_id, command_name) -> timestamp of last execution
        self._last_executed: Dict[Tuple[int, str], float] = {}

    def get_remaining_cooldown(self, user_id: int, command_name: str, cooldown_duration: float) -> float:
        """Returns the remaining cooldown time in seconds.

        Returns 0.0 if the command is not on cooldown.
        """
        key = (user_id, command_name)
        if key not in self._last_executed:
            return 0.0
        
        elapsed = time.time() - self._last_executed[key]
        remaining = cooldown_duration - elapsed
        return max(0.0, remaining)

    def update_cooldown(self, user_id: int, command_name: str):
        """Updates the cooldown timestamp to the current time."""
        self._last_executed[(user_id, command_name)] = time.time()

    def reset_cooldown(self, user_id: int, command_name: str):
        """Removes the cooldown entry, resetting it (e.g., if a command failed to start)."""
        self._last_executed.pop((user_id, command_name), None)

# Global cooldown manager instance
cooldown_manager = CooldownManager()
