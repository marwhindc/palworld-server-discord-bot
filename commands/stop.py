import asyncio
import time
import discord
from discord.ext import commands
from discord import app_commands
from services.permissions import check_admin_only
from utils.cooldown import cooldown_manager
from utils.embeds import success_embed, info_embed, error_embed
from utils.logger import bot_logger

class StopCog(commands.Cog):
    """Cog handling the /stop command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.gcp_service = bot.gcp_service
        self.palworld_service = bot.palworld_service
        self.usage_service = bot.usage_service

    @app_commands.command(name="stop", description="Stops the Palworld server and virtual machine (Admins only).")
    @check_admin_only()
    async def stop_server(self, interaction: discord.Interaction):
        config = self.bot.config
        user = interaction.user
        
        bot_logger.info(f"User {user.name} ({user.id}) issued command: /stop")

        # 1. Cooldown Protection
        remaining = cooldown_manager.get_remaining_cooldown(user.id, "stop", config.STOP_COOLDOWN)
        if remaining > 0:
            await interaction.response.send_message(
                embed=error_embed(
                    "Command Cooldown",
                    f"This command is on cooldown. Please try again in {int(remaining)} seconds."
                ),
                ephemeral=True
            )
            return

        # 2. Check VM Status
        try:
            status = await self.gcp_service.get_instance_status()
        except Exception as e:
            await interaction.response.send_message(
                embed=error_embed(
                    "GCP Status Check Failed",
                    f"Failed to check VM status: {e}"
                ),
                ephemeral=True
            )
            return

        if status != "RUNNING":
            await interaction.response.send_message(
                embed=success_embed(
                    "Server Already Stopped",
                    f"The hosting VM is already in `{status}` state."
                )
            )
            return

        # 3. Check for active players if Palworld service is online
        ip = await self.gcp_service.get_external_ip()
        palworld_online = await self.palworld_service.is_server_online(ip)
        if palworld_online:
            try:
                players = await self.palworld_service.get_players(ip)
                if len(players) > 0:
                    player_names = ", ".join([p.get("name", "Unknown") for p in players])
                    await interaction.response.send_message(
                        embed=error_embed(
                            "Shutdown Refused",
                            f"There are currently active players connected to the server:\n`{player_names}`\n"
                            "You cannot stop the server while players are online."
                        )
                    )
                    return
            except Exception as e:
                await interaction.response.send_message(
                    embed=error_embed(
                        "Verification Failed",
                        f"Failed to check active player list before stopping: {e}\n"
                        "Shutdown aborted for safety."
                    ),
                    ephemeral=True
                )
                return

        # 4. Perform Shutdown
        cooldown_manager.update_cooldown(user.id, "stop")

        # Respond immediately that shutdown has begun
        await interaction.response.send_message(
            embed=info_embed(
                "Stopping Server",
                "Initiating server shutdown sequence..."
            )
        )

        shutdown_start_time = time.time()

        # Stop Palworld Service first if it is online
        if palworld_online:
            await interaction.followup.send(
                embed=info_embed(
                    "Palworld Shutdown",
                    "Sending graceful shutdown request to Palworld server..."
                )
            )
            # Send shutdown command (5-second grace period)
            success = await self.palworld_service.shutdown(waittime=5, message="Discord /stop command triggered. Saving & Shutting down.", ip=ip)
            if success:
                # Wait for Palworld service to stop responding (or up to 10 seconds)
                for _ in range(10):
                    await asyncio.sleep(1)
                    if not await self.palworld_service.is_server_online(ip):
                        break
            else:
                await interaction.followup.send(
                    embed=error_embed(
                        "Graceful Shutdown Failed",
                        "Could not shutdown the Palworld service gracefully. Attempting VM force termination anyway..."
                    )
                )

        # Stop the VM
        await interaction.followup.send(
            embed=info_embed(
                "GCP VM Shutdown",
                "Stopping the virtual machine instance..."
            )
        )

        try:
            await self.gcp_service.stop_instance()
        except Exception as e:
            # We do NOT reset the cooldown here as the Palworld service might have already been terminated.
            await interaction.followup.send(
                embed=error_embed(
                    "VM Stop Failure",
                    f"Failed to request VM instance stop from Google Cloud: {e}"
                )
            )
            return

        # Poll VM until stopped
        vm_stopped = await self.gcp_service.wait_until_stopped(timeout=120)
        if not vm_stopped:
            await interaction.followup.send(
                embed=error_embed(
                    "VM Shutdown Timeout",
                    "The virtual machine instance is taking longer than expected to stop. Please check Google Cloud Console."
                )
            )
            return

        self.usage_service.record_stop()

        shutdown_duration = time.time() - shutdown_start_time
        bot_logger.info(f"Palworld server successfully stopped in {shutdown_duration:.1f} seconds.")

        # Final Confirmation
        await interaction.followup.send(
            embed=success_embed(
                "Server Stopped",
                f"The Palworld server and virtual machine have been shut down successfully!\n\n"
                f"**Shutdown Duration:** `{int(shutdown_duration)}` seconds\n"
                f"**Current Status:** `OFFLINE`"
            )
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(StopCog(bot))
