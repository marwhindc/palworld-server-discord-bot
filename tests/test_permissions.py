import unittest
from unittest.mock import MagicMock
import discord
from config import Config
from services import permissions

class TestPermissions(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock(spec=Config)
        self.config.ALLOWED_CHANNEL_ID = 12345
        self.config.ALLOWED_ROLE = "PalworldPlayers"
        
        self.interaction = MagicMock()
        self.interaction.channel_id = 12345
        
        self.user = MagicMock(spec=discord.Member)
        self.interaction.user = self.user
        
        # Default non-admin permissions
        self.user.guild_permissions.administrator = False
        
        self.role1 = MagicMock()
        self.role1.name = "OtherRole"
        self.role1.id = 111
        
        self.role2 = MagicMock()
        self.role2.name = "PalworldPlayers"
        self.role2.id = 222
        
        self.user.roles = [self.role1]

    def test_is_correct_channel(self):
        """Verifies channel matching logic."""
        self.assertTrue(permissions.is_correct_channel(self.interaction, self.config))
        self.interaction.channel_id = 99999
        self.assertFalse(permissions.is_correct_channel(self.interaction, self.config))

    def test_has_allowed_role_success_name(self):
        """Verifies matching role by role name."""
        self.user.roles = [self.role1, self.role2]
        self.assertTrue(permissions.has_allowed_role(self.interaction, self.config))

    def test_has_allowed_role_success_id(self):
        """Verifies matching role by role ID (string)."""
        self.config.ALLOWED_ROLE = "222"
        self.user.roles = [self.role1, self.role2]
        self.assertTrue(permissions.has_allowed_role(self.interaction, self.config))

    def test_has_allowed_role_fail(self):
        """Verifies access failure if user does not have the target role."""
        self.user.roles = [self.role1]
        self.assertFalse(permissions.has_allowed_role(self.interaction, self.config))

    def test_has_allowed_role_bypass_admin(self):
        """Verifies that administrator guild permission bypasses role requirement."""
        self.user.guild_permissions.administrator = True
        self.user.roles = [self.role1]  # No allowed role in list
        self.assertTrue(permissions.has_allowed_role(self.interaction, self.config))

    def test_is_administrator(self):
        """Verifies identification of administrator privilege levels."""
        self.assertFalse(permissions.is_administrator(self.interaction))
        self.user.guild_permissions.administrator = True
        self.assertTrue(permissions.is_administrator(self.interaction))

if __name__ == "__main__":
    unittest.main()
