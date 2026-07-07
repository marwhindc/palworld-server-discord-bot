import discord
from discord.ext import commands
from discord import app_commands
from services.permissions import check_channel_and_role
from utils.embeds import success_embed
from utils.logger import bot_logger

class CostCog(commands.Cog):
    """Cog handling the /cost command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.usage_service = bot.usage_service

    @app_commands.command(name="cost", description="Checks the estimated Google Cloud costs incurred by the server this month.")
    @check_channel_and_role()
    async def check_cost(self, interaction: discord.Interaction):
        config = self.bot.config
        bot_logger.info(f"User {interaction.user.name} ({interaction.user.id}) issued command: /cost")

        # Defer response as we load the usage database
        await interaction.response.defer()

        # Calculate estimated costs
        cost_details = self.usage_service.calculate_estimated_cost(config)
        hours = cost_details["hours"]
        compute_cost = cost_details["compute_cost"]
        storage_cost = cost_details["storage_cost"]
        total_cost = cost_details["total_cost"]

        # Assume standard $300 GCP starter trial credit limit
        trial_limit = 300.0
        remaining_credit = max(0.0, trial_limit - total_cost)

        fields = [
            {
                "name": "⏱️ VM Active Hours",
                "value": f"`{hours:.2f}` hours",
                "inline": True
            },
            {
                "name": "💻 Compute Cost",
                "value": f"`${compute_cost:.2f}`\n*(Rate: ${config.VM_HOURLY_RATE:.4f}/hr)*",
                "inline": True
            },
            {
                "name": "📁 Storage Cost",
                "value": f"`${storage_cost:.2f}`\n*({config.DISK_SIZE_GB} GB Balanced PD)*",
                "inline": True
            },
            {
                "name": "💰 Total Spent This Month",
                "value": f"**`${total_cost:.2f}`**",
                "inline": False
            },
            {
                "name": "🎁 Remaining Free Trial Credit",
                "value": f"**`${remaining_credit:.2f}`** / `${trial_limit:.0f}`",
                "inline": False
            }
        ]

        # Return the billing summary embed
        await interaction.followup.send(
            embed=success_embed(
                "Estimated Google Cloud Cost Summary",
                description="This month's approximate billing estimates based on VM runtime hours and storage allocation:",
                fields=fields
            )
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(CostCog(bot))
