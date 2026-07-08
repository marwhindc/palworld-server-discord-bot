import discord
from discord.ext import commands
from discord import app_commands
from services.permissions import check_channel_and_role
from utils.embeds import success_embed
from utils.logger import bot_logger

class HelpCog(commands.Cog):
    """Cog handling the /help command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Displays available commands with detailed descriptions.")
    @check_channel_and_role()
    async def help_command(self, interaction: discord.Interaction):
        bot_logger.info(f"User {interaction.user.name} ({interaction.user.id}) issued command: /help")
        config = self.bot.config

        fields = [
            {
                "name": "🚀 `/start`",
                "value": "Starts the GCE virtual machine and boots the Palworld dedicated server.\n"
                         f"• *Permissions:* Member must have `{config.ALLOWED_ROLE}` role\n"
                         f"• *Cooldown:* `{int(config.START_COOLDOWN / 60)}` minutes",
                "inline": False
            },
            {
                "name": "📊 `/status`",
                "value": "Displays real-time status, including VM power state, REST API status, uptime, player counts, FPS, and connection details.",
                "inline": False
            },
            {
                "name": "👥 `/players`",
                "value": "Displays a list of currently online players, including Steam IDs, levels, and connection latency.",
                "inline": False
            },
            {
                "name": "🛑 `/stop`",
                "value": "Gracefully shuts down the Palworld game service and stops the GCE virtual machine instance.\n"
                         "• *Permissions:* **Administrators only**\n"
                         f"• *Cooldown:* `{int(config.STOP_COOLDOWN / 60)}` minutes",
                "inline": False
            },
            {
                "name": "💰 `/cost`",
                "value": "Checks the estimated Google Cloud costs incurred by the server this month.\n"
                         f"• *Permissions:* Member must have `{config.ALLOWED_ROLE}` role",
                "inline": False
            },
            {
                "name": "❓ `/help`",
                "value": "Displays this help menu with commands, requirements, and permissions.",
                "inline": False
            }
        ]

        description = (
            "Welcome to the **Palworld Server Manager** Discord Bot!\n\n"
            f"**Channel Restriction:** Commands are restricted to <#{config.ALLOWED_CHANNEL_ID}>.\n"
            "Here is the list of available slash commands:"
        )

        await interaction.response.send_message(
            embed=success_embed(
                "Bot Commands & Manual",
                description=description,
                fields=fields
            )
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
