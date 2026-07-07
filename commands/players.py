import discord
from discord.ext import commands
from discord import app_commands
from services.permissions import check_channel_and_role
from utils.embeds import success_embed, error_embed
from utils.logger import bot_logger

class PlayersCog(commands.Cog):
    """Cog handling the /players command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.gcp_service = bot.gcp_service
        self.palworld_service = bot.palworld_service

    @app_commands.command(name="players", description="Lists details of all players currently connected to the server.")
    @check_channel_and_role()
    async def list_players(self, interaction: discord.Interaction):
        bot_logger.info(f"User {interaction.user.name} ({interaction.user.id}) issued command: /players")

        # Defer response to handle API call latency
        await interaction.response.defer()

        # 1. Check VM status first
        try:
            vm_status = await self.gcp_service.get_instance_status()
        except Exception as e:
            await interaction.followup.send(
                embed=error_embed(
                    "GCP Query Failure",
                    f"Failed to query VM status: {e}"
                )
            )
            return

        if vm_status != "RUNNING":
            await interaction.followup.send(
                embed=error_embed(
                    "Server Offline",
                    "The hosting VM is stopped. No players can be connected."
                )
            )
            return

        # 2. Check if Palworld REST API is online
        ip = await self.gcp_service.get_external_ip()
        is_online = await self.palworld_service.is_server_online(ip)
        if not is_online:
            await interaction.followup.send(
                embed=error_embed(
                    "Server Unreachable",
                    "The hosting VM is running, but the Palworld service is not responding. The server may be booting up."
                )
            )
            return

        # 3. Retrieve players
        try:
            players = await self.palworld_service.get_players(ip)
        except Exception as e:
            await interaction.followup.send(
                embed=error_embed(
                    "API Query Failure",
                    f"Failed to retrieve players list: {e}"
                )
            )
            return

        if not players:
            await interaction.followup.send(
                embed=success_embed(
                    "Online Players",
                    "There are currently **0** players connected to the server."
                )
            )
            return

        # 4. Render players details
        fields = []
        for i, player in enumerate(players, start=1):
            name = player.get("name", "Unknown Player")
            steam_id = player.get("userId", "N/A")
            level = player.get("level", "N/A")
            ping = player.get("ping", "N/A")
            
            # Format ping if it's numeric
            ping_str = f"{ping:.1f}ms" if isinstance(ping, (int, float)) else f"{ping}"

            fields.append({
                "name": f"{i}. {name}",
                "value": f"• **Steam ID:** `{steam_id}`\n• **Level:** `{level}`\n• **Ping:** `{ping_str}`",
                "inline": False
            })

        await interaction.followup.send(
            embed=success_embed(
                "Online Players",
                description=f"Showing active players count: **{len(players)}**",
                fields=fields
            )
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(PlayersCog(bot))
