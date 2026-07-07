import time
import discord
from discord.ext import commands
from discord import app_commands
from services.permissions import check_channel_and_role
from utils.cooldown import cooldown_manager
from utils.embeds import success_embed, info_embed, error_embed
from utils.logger import bot_logger

class StartCog(commands.Cog):
    """Cog handling the /start command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Services will be resolved from the bot instance
        self.gcp_service = bot.gcp_service
        self.palworld_service = bot.palworld_service
        self.usage_service = bot.usage_service

    @app_commands.command(name="start", description="Starts the GCE VM and Palworld server.")
    @check_channel_and_role()
    async def start_server(self, interaction: discord.Interaction):
        config = self.bot.config
        user = interaction.user
        
        bot_logger.info(f"User {user.name} ({user.id}) issued command: /start")

        # 1. Cooldown Protection
        remaining = cooldown_manager.get_remaining_cooldown(user.id, "start", config.START_COOLDOWN)
        if remaining > 0:
            await interaction.response.send_message(
                embed=error_embed(
                    "Command Cooldown",
                    f"This command is on cooldown. Please try again in {int(remaining)} seconds."
                ),
                ephemeral=True
            )
            return

        # 2. Check VM and Palworld Status
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

        if status == "RUNNING":
            self.usage_service.record_start()
            online = await self.palworld_service.is_server_online()
            if online:
                ip = await self.gcp_service.get_external_ip() or "Unknown IP"
                player_count = await self.palworld_service.get_player_count()
                await interaction.response.send_message(
                    embed=success_embed(
                        "Server Already Running",
                        f"The server is already running and fully operational!\n\n"
                        f"**IP:** `{ip}`\n"
                        f"**Port:** `8211`\n"
                        f"**Current Players:** `{player_count}`"
                    )
                )
                return
            else:
                # VM is running but Palworld REST API is not online yet
                await interaction.response.send_message(
                    embed=info_embed(
                        "VM Active - Waiting for Palworld",
                        "The virtual machine is running, but the Palworld service is still initializing. Polling API..."
                    )
                )
                
                # Cooldown set since we are waiting/running
                cooldown_manager.update_cooldown(user.id, "start")
                
                api_ready = await self.palworld_service.wait_until_ready(timeout=180)
                if api_ready:
                    ip = await self.gcp_service.get_external_ip() or "Unknown IP"
                    await interaction.followup.send(
                        embed=success_embed(
                            "Server Ready",
                            f"The Palworld server has finished initializing!\n\n"
                            f"**IP:** `{ip}`\n"
                            f"**Port:** `8211`\n"
                            f"**Current Players:** `0`"
                        )
                    )
                else:
                    cooldown_manager.reset_cooldown(user.id, "start")
                    await interaction.followup.send(
                        embed=error_embed(
                            "Startup Timeout",
                            "The VM is online, but the Palworld game service failed to respond in time."
                        )
                    )
                return

        # 3. If VM is not running, start it
        cooldown_manager.update_cooldown(user.id, "start")
        
        # Respond immediately that startup has begun
        await interaction.response.send_message(
            embed=info_embed(
                "Starting Server",
                "Booting the Google Cloud virtual machine..."
            )
        )

        start_time = time.time()
        try:
            await self.gcp_service.start_instance()
        except Exception as e:
            cooldown_manager.reset_cooldown(user.id, "start")
            await interaction.followup.send(
                embed=error_embed(
                    "VM Start Failure",
                    f"Failed to initiate VM startup: {e}"
                )
            )
            return

        # Poll VM status until running
        vm_ready = await self.gcp_service.wait_until_running(timeout=120)
        if not vm_ready:
            cooldown_manager.reset_cooldown(user.id, "start")
            await interaction.followup.send(
                embed=error_embed(
                    "VM Startup Timeout",
                    "The Google Cloud VM did not transition to RUNNING state in a timely manner."
                )
            )
            return

        self.usage_service.record_start()

        # Fetch IP
        ip = await self.gcp_service.get_external_ip() or "Unknown IP"

        # Update status
        await interaction.followup.send(
            embed=info_embed(
                "VM Active - Booting Game Server",
                f"Virtual machine is now RUNNING at `{ip}`.\nWaiting for the Palworld game service to boot..."
            )
        )

        # Poll Palworld REST API until responsive
        api_ready = await self.palworld_service.wait_until_ready(timeout=180)
        if not api_ready:
            # We don't reset cooldown here because the VM did start and is running,
            # which consumes resources and prevents startup spamming.
            await interaction.followup.send(
                embed=error_embed(
                    "Game Service Timeout",
                    f"VM is running at `{ip}`, but the Palworld server REST API is not responding. "
                    "It might still be loading database assets."
                )
            )
            return

        startup_duration = time.time() - start_time
        bot_logger.info(f"Palworld server successfully started in {startup_duration:.1f} seconds.")

        # Final Success Report
        await interaction.followup.send(
            embed=success_embed(
                "Server Ready",
                f"The Palworld dedicated server is online!\n\n"
                f"**IP:** `{ip}`\n"
                f"**Port:** `8211`\n"
                f"**Estimated Startup Time:** `{int(startup_duration)}` seconds\n"
                f"**Current Players:** `0`"
            )
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(StartCog(bot))
