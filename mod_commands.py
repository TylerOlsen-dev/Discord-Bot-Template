import discord
from discord.ext import commands
from discord import app_commands


class ModeratorCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Ban Command
    @discord.app_commands.command(
        name="ban",
        description="Ban a user from the server."
    )
    @discord.app_commands.describe(
        member="The member to ban",
        reason="The reason for the ban"
    )
    @discord.app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided"
    ):
        await member.ban(reason=reason)
        await interaction.response.send_message(
            f"{member.display_name} has been banned for: {reason}", ephemeral=True
        )

    # Kick Command
    @discord.app_commands.command(
        name="kick",
        description="Kick a user from the server."
    )
    @discord.app_commands.describe(
        member="The member to kick",
        reason="The reason for kicking the member"
    )
    @discord.app_commands.checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided"
    ):
        await member.kick(reason=reason)
        await interaction.response.send_message(
            f"{member.display_name} has been kicked. Reason: {reason}"
        )

    # Unban Command
    @app_commands.command(
        name="unban",
        description="Unban a member from the server."
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(
        self,
        interaction: discord.Interaction,
        user: discord.User
    ):
        banned_users = await interaction.guild.bans()
        for ban_entry in banned_users:
            if ban_entry.user == user:
                await interaction.guild.unban(user)
                await interaction.response.send_message(
                    f"{user.mention} has been unbanned."
                )
                return
        await interaction.response.send_message(
            f"{user.mention} is not banned."
        )

    # Mute Command
    @app_commands.command(
        name="mute",
        description="Mute a member in the server."
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def mute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = None
    ):
        mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
        if not mute_role:
            mute_role = await interaction.guild.create_role(name="Muted")
            for channel in interaction.guild.channels:
                await channel.set_permissions(
                    mute_role,
                    speak=False,
                    send_messages=False,
                    read_message_history=True,
                    read_messages=False
                )
        await member.add_roles(mute_role, reason=reason)
        await interaction.response.send_message(
            f"{member.mention} has been muted for {reason}."
        )

    # Unmute Command
    @app_commands.command(
        name="unmute",
        description="Unmute a member in the server."
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def unmute(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):
        mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
        if mute_role in member.roles:
            await member.remove_roles(mute_role)
            await interaction.response.send_message(
                f"{member.mention} has been unmuted."
            )
        else:
            await interaction.response.send_message(
                f"{member.mention} is not muted."
            )

    # Purge Command
    @app_commands.command(
        name="purge",
        description="Purge a number of messages from a channel."
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(
        self,
        interaction: discord.Interaction,
        amount: int
    ):
        await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(
            f"Purged {amount} messages.", ephemeral=True
        )

    # Announce Command
    @app_commands.command(
        name="announce",
        description="Send an announcement to a specific channel."
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def announce(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        *,
        message: str
    ):
        await channel.send(message)
        await interaction.response.send_message(
            f"Announcement sent to {channel.mention}", ephemeral=True
        )

    # Warn Command
    @app_commands.command(
        name="warn",
        description="Warn a member in the server."
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        *,
        reason: str = None
    ):
        await interaction.response.send_message(
            f"{member.mention} has been warned for {reason}.", ephemeral=True
        )
        await member.send(
            f"You have been warned in {interaction.guild.name} for: {reason}"
        )

    # List Warnings Command
    @app_commands.command(
        name="warns",
        description="List all warnings for a member."
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warns(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):
        # Placeholder for warn listing logic
        await interaction.response.send_message(
            f"{member.mention} has no warnings.", ephemeral=True
        )

    # Give Role Command
    @app_commands.command(
        name="give",
        description="Give a role to multiple users."
    )
    @app_commands.describe(
        role="The role you want to assign",
        users="The users to give the role to, separated by spaces."
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def give_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        users: str
    ):
        await interaction.response.defer(ephemeral=True)
        user_ids = [user_id.strip() for user_id in users.split(' ')]
        success_users = []
        failed_users = []
        for user_id in user_ids:
            try:
                user = await interaction.guild.fetch_member(int(user_id.strip('<@!>')))
                if role.position < interaction.guild.me.top_role.position:
                    await user.add_roles(role)
                    success_users.append(user.display_name)
                else:
                    failed_users.append(user_id)
            except (discord.NotFound, discord.Forbidden, ValueError):
                failed_users.append(user_id)
        messages = []
        if success_users:
            messages.append(
                f"Successfully given {role.name} to {', '.join(success_users)}."
            )
        if failed_users:
            messages.append(
                f"Failed to give {role.name} to {', '.join(failed_users)}. "
                "Check if they're valid users and if I have the correct permissions."
            )
        for message in messages:
            await interaction.followup.send(
                message,
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none()
            )

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user}')

async def setup(bot):
    await bot.add_cog(ModeratorCommands(bot))
