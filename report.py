import discord
from discord.ext import commands

# --- Configuration Values ---
MOD_CHANNEL_ID = 123456789012345678  # Replace with your mod channel ID

# --- End of Configuration Values ---

class ReportCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(
        name="report",
        description="Report a user"
    )
    @discord.app_commands.describe(
        user="The user you want to report",
        reason="The reason for reporting the user"
    )
    async def report(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        reason: str
    ):
        mod_channel = self.bot.get_channel(MOD_CHANNEL_ID)
        if mod_channel:
            await mod_channel.send(
                f"Report received:\nReporter: {interaction.user}\nReported User: {user}\nReason: {reason}"
            )
            await interaction.response.send_message(
                "Thank you for your report. Our moderators will review it shortly.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Mod channel not found. Please contact an admin.", ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(ReportCommand(bot))
