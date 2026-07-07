import discord
from discord import app_commands
from config import Config

class WrongChannelError(app_commands.AppCommandError):
    """Raised when a command is run in an unauthorized channel."""
    pass

class MissingRoleError(app_commands.AppCommandError):
    """Raised when a user lacks the allowed role to control the server."""
    pass

class NotAdministratorError(app_commands.AppCommandError):
    """Raised when a non-admin tries to run admin-only commands."""
    pass

def is_correct_channel(interaction: discord.Interaction, config: Config) -> bool:
    """Checks if the command is run in the allowed channel."""
    return interaction.channel_id == config.ALLOWED_CHANNEL_ID

def has_allowed_role(interaction: discord.Interaction, config: Config) -> bool:
    """Checks if the user has the required role (name or ID) or is an administrator."""
    user = interaction.user
    if not isinstance(user, discord.Member):
        return False
        
    # Administrators bypass standard role checks
    if user.guild_permissions.administrator:
        return True

    role_spec = config.ALLOWED_ROLE
    for role in user.roles:
        if role.name == role_spec or str(role.id) == role_spec:
            return True
            
    return False

def is_administrator(interaction: discord.Interaction) -> bool:
    """Checks if the user has Administrator guild permissions."""
    user = interaction.user
    if not isinstance(user, discord.Member):
        return False
    return user.guild_permissions.administrator

def check_channel_and_role():
    """Decorator to enforce channel and role permissions dynamically."""
    def predicate(interaction: discord.Interaction) -> bool:
        config = getattr(interaction.client, "config", None)
        if not config:
            return True
        if not is_correct_channel(interaction, config):
            raise WrongChannelError(f"This command can only be used in <#{config.ALLOWED_CHANNEL_ID}>.")
        if not has_allowed_role(interaction, config):
            raise MissingRoleError(f"You require the `{config.ALLOWED_ROLE}` role to use this command.")
        return True
    return app_commands.check(predicate)

def check_admin_only():
    """Decorator to enforce channel and admin-only permissions dynamically."""
    def predicate(interaction: discord.Interaction) -> bool:
        config = getattr(interaction.client, "config", None)
        if not config:
            return True
        if not is_correct_channel(interaction, config):
            raise WrongChannelError(f"This command can only be used in <#{config.ALLOWED_CHANNEL_ID}>.")
        if not is_administrator(interaction):
            raise NotAdministratorError("Only server administrators can use this command.")
        return True
    return app_commands.check(predicate)
