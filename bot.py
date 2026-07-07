import sys
import asyncio
import discord
from discord.ext import commands, tasks
from discord import app_commands
from config import Config
from services.gcp import GCPService
from services.palworld import PalworldService
from services.usage import UsageService
from utils.logger import bot_logger
from utils.embeds import error_embed

class PalworldBot(commands.Bot):
    """Custom commands.Bot instance integrating services and configuration."""

    def __init__(self, config: Config):
        # standard intents
        intents = discord.Intents.default()
        
        super().__init__(command_prefix="!", intents=intents)
        self.config = config
        
        # Inject GCP, Palworld, and Usage services
        self.gcp_service = GCPService(
            project_id=config.GCP_PROJECT_ID,
            zone=config.GCP_ZONE,
            instance_name=config.INSTANCE_NAME
        )
        self.palworld_service = PalworldService(
            rest_url=config.PALWORLD_REST_URL,
            username=config.PALWORLD_REST_USERNAME,
            password=config.PALWORLD_REST_PASSWORD
        )
        self.usage_service = UsageService()

    @tasks.loop(minutes=5.0)
    async def update_active_usage(self):
        """Periodically flushes running time for active VM sessions to prevent data loss."""
        try:
            await asyncio.to_thread(self.usage_service.update_active_session)
        except Exception as e:
            bot_logger.error(f"Error in background active usage update task: {e}")

    async def setup_hook(self):
        """Standard discord.py hook to load extensions and sync command tree."""
        initial_extensions = [
            "commands.start",
            "commands.status",
            "commands.players",
            "commands.stop",
            "commands.help",
            "commands.cost"
        ]
        
        # Start background task loop
        self.update_active_usage.start()
        
        for ext in initial_extensions:
            try:
                await self.load_extension(ext)
                bot_logger.info(f"Successfully loaded extension: {ext}")
            except Exception as e:
                bot_logger.error(f"Failed to load extension {ext}: {e}", exc_info=True)

        # Sync command tree with Discord
        try:
            bot_logger.info("Syncing application command tree...")
            await self.tree.sync()
            bot_logger.info("Application command tree synced successfully.")
        except Exception as e:
            bot_logger.error(f"Failed to sync command tree: {e}", exc_info=True)

def setup_global_error_handler(bot: PalworldBot):
    """Registers standard application command error handler."""
    
    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        from services.permissions import WrongChannelError, MissingRoleError, NotAdministratorError
        
        # Resolve destination responder function (handle deferred responses)
        send_func = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
        
        # Unwrap Transformer/Check failure errors
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        if isinstance(error, WrongChannelError):
            await send_func(
                embed=error_embed("Wrong Channel", str(error)),
                ephemeral=True
            )
            bot_logger.warning(f"User {interaction.user} tried to run a command in an unauthorized channel: {error}")
            
        elif isinstance(error, MissingRoleError):
            await send_func(
                embed=error_embed("Missing Permissions", str(error)),
                ephemeral=True
            )
            bot_logger.warning(f"User {interaction.user} lacked role: {error}")
            
        elif isinstance(error, NotAdministratorError):
            await send_func(
                embed=error_embed("Access Denied", str(error)),
                ephemeral=True
            )
            bot_logger.warning(f"User {interaction.user} failed Administrator check: {error}")
            
        elif isinstance(error, app_commands.CommandOnCooldown):
            await send_func(
                embed=error_embed("Command Cooldown", f"This command is on cooldown. Try again in {error.retry_after:.1f}s."),
                ephemeral=True
            )
            
        else:
            bot_logger.error(f"Unhandled Slash Command exception: {error}", exc_info=True)
            try:
                await send_func(
                    embed=error_embed("Command Error", f"An unexpected error occurred: {error}"),
                    ephemeral=True
                )
            except Exception:
                pass

def main():
    try:
        config = Config.load_from_env()
    except ValueError as e:
        bot_logger.critical(f"Configuration failed to initialize: {e}")
        sys.exit(1)
        
    bot = PalworldBot(config)
    setup_global_error_handler(bot)
    
    @bot.event
    async def on_ready():
        bot_logger.info(f"Bot successfully authenticated as: {bot.user.name} (ID: {bot.user.id})")
        bot_logger.info("Palworld Discord Bot is now fully online.")

    # Start bot
    bot_logger.info("Authenticating and launching bot...")
    bot.run(config.DISCORD_TOKEN)

if __name__ == "__main__":
    main()
