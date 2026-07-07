import discord
from discord.ext import commands
from discord import app_commands
from services.permissions import check_channel_and_role
from utils.embeds import success_embed, error_embed
from utils.logger import bot_logger

def format_uptime(seconds: float) -> str:
    """Formats seconds into a human-readable string (e.g. 1d 4h 23m 10s)."""
    seconds = int(seconds)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
        
    return " ".join(parts)

class StatusCog(commands.Cog):
    """Cog handling the /status command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.gcp_service = bot.gcp_service
        self.palworld_service = bot.palworld_service

    @app_commands.command(name="status", description="Checks the real-time status of the GCE VM and Palworld server.")
    @check_channel_and_role()
    async def server_status(self, interaction: discord.Interaction):
        config = self.bot.config
        bot_logger.info(f"User {interaction.user.name} ({interaction.user.id}) issued command: /status")

        # Defer the response since getting GCP VM status and REST API details might take a few seconds
        await interaction.response.defer()

        try:
            # 1. Fetch GCE VM Status
            vm_status = await self.gcp_service.get_instance_status()
        except Exception as e:
            await interaction.followup.send(
                embed=error_embed(
                    "GCP Query Failure",
                    f"Failed to query VM status: {e}"
                )
            )
            return

        # Handle Stopped/Off VM States
        if vm_status != "RUNNING":
            fields = [
                {"name": "VM State", "value": f"🔴 `{vm_status}`", "inline": True},
                {"name": "Palworld State", "value": "🔴 `OFFLINE`", "inline": True},
                {"name": "Zone", "value": f"`{config.GCP_ZONE}`", "inline": True}
            ]
            await interaction.followup.send(
                embed=error_embed(
                    "Server Offline",
                    description="The hosting virtual machine is currently powered down.",
                    fields=fields
                )
            )
            return

        # 2. VM is Running - Gather Further Details
        ip = await self.gcp_service.get_external_ip()
        
        # Check Palworld REST API
        is_online = await self.palworld_service.is_server_online(ip)
        
        if not is_online:
            fields = [
                {"name": "VM State", "value": "🟢 `RUNNING`", "inline": True},
                {"name": "Palworld State", "value": "🟡 `STARTING/OFFLINE`", "inline": True},
                {"name": "Zone", "value": f"`{config.GCP_ZONE}`", "inline": True},
                {"name": "External IP", "value": f"`{ip or 'Unknown IP'}`", "inline": True},
                {"name": "Port", "value": "`8211`", "inline": True}
            ]
            await interaction.followup.send(
                embed=success_embed(
                    "Server Starting",
                    description="The hosting VM is online, but the Palworld service is not yet responding to requests.",
                    fields=fields
                )
            )
            return

        # 3. Server is online - Get metrics
        metrics = await self.palworld_service.get_metrics(ip)
        
        if metrics:
            players_online = metrics.get("currentplayernum", 0)
            max_players = metrics.get("maxplayernum", 32)
            uptime_seconds = metrics.get("uptime", 0)
            server_fps = metrics.get("serverfps", 0)
            
            uptime_str = format_uptime(uptime_seconds)
            player_str = f"`{players_online} / {max_players}`"
            fps_str = f"`{server_fps:.1f}`" if isinstance(server_fps, (int, float)) else f"`{server_fps}`"
        else:
            # Fallback if metrics endpoints fails but is_online succeeded
            players_online = await self.palworld_service.get_player_count(ip)
            player_str = f"`{players_online}`"
            uptime_str = "`N/A`"
            fps_str = "`N/A`"

        fields = [
            {"name": "VM State", "value": "🟢 `RUNNING`", "inline": True},
            {"name": "Palworld State", "value": "🟢 `ONLINE`", "inline": True},
            {"name": "Uptime", "value": f"`{uptime_str}`", "inline": True},
            {"name": "Players", "value": player_str, "inline": True},
            {"name": "Server FPS", "value": fps_str, "inline": True},
            {"name": "Zone", "value": f"`{config.GCP_ZONE}`", "inline": True},
            {"name": "IP Address", "value": f"`{ip}`", "inline": True},
            {"name": "Connection Port", "value": "`8211`", "inline": True}
        ]

        await interaction.followup.send(
            embed=success_embed(
                "Server Status",
                description="The server is online and healthy.",
                fields=fields
            )
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(StatusCog(bot))
