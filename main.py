# Main imports
import logging
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import os
import aiofiles

# --- Configuration Values ---
# Replace the following placeholders with your actual values

BOT_TOKEN = 'YOUR_BOT_TOKEN'  # Replace with your bot token
GUILD_ID = 123456789012345678  # Replace with your guild ID
VERIFIED_ROLE_ID = 123456789012345678  # Replace with your verified role ID
UNVERIFIED_ROLE_ID = 123456789012345678  # Replace with your unverified role ID
MOD_ROLE_NAME = "MODERATOR_ROLE_NAME"  # Replace with your moderator role name
ADMIN_ROLE_NAME = "ADMINISTRATOR_ROLE_NAME"  # Replace with your administrator role name
TICKET_BUTTON_MESSAGE_ID = 123456789012345678  # Replace with the ticket button message ID after the first run
TICKET_CHANNEL_ID = 123456789012345678  # Replace with the channel ID where the ticket button should be sent

# --- End of Configuration Values ---

# Setup logging
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s'
)

# Define the required intents for the bot
intents = discord.Intents.default()
intents.guilds = True
intents.members = True  # Required for member events and role management
intents.messages = True
intents.reactions = True
intents.message_content = True

# Initialize the bot with the specified command prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents)

async def load_extensions():
    extensions = [
        'mod_commands',
        'non_mod',
        'role_selection',
        'report'
    ]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            logging.info(f"Loaded extension '{ext}' successfully.")
        except Exception as e:
            logging.error(f"Failed to load extension '{ext}'. Reason: {e}")

@bot.event
async def on_command_completion(ctx):
    logging.info(
        f"Command: {ctx.command} executed by {ctx.author} in {ctx.channel}"
    )

@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command: discord.app_commands.Command):
    logging.info(
        f"Slash Command: {command.name} executed by {interaction.user} in {interaction.channel}"
    )

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help", description="List all commands and their descriptions."
    )
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Help - List of Commands", color=discord.Color.blue()
        )
        commands_info = [
            ("verify", "Verify your identity to access the server.", False),
            ("ban", "Ban a member.", True),
            ("ban_role", "Ban all members with a specific role.", True),
            ("kick", "Kick a member.", True),
            ("kick_role", "Kick all members with a specific role.", True),
            ("unban", "Unban a member from the server.", True),
            ("mute", "Mute a member in the server.", True),
            ("unmute", "Unmute a member in the server.", True),
            ("purge", "Purge a number of messages from a channel.", True),
            ("announce", "Send an announcement to a specific channel.", True),
            ("warn", "Warn a member in the server.", True),
            ("warns", "List all warnings for a member.", True),
            ("give", "Give a role to multiple users.", True),
            ("compliment", "Compliment a user.", False),
            ("eight_ball", "Ask the Magic 8-Ball a question.", False),
            ("hello", "Receive a greeting from the bot.", False),
            ("level", "Check your level or another person’s level.", False),
            ("report", "Report a user.", False),
            ("set_roles", "Set roles and associated questions.", True),
            ("list_questions", "List all set questions.", True),
            ("remove_question", "Remove a specific question by number.", True),
            ("pick_role", "Pick a role based on a question.", False),
            ("remove_role", "Remove a role.", False),
            ("verify_user", "Verify a user by assigning roles and closing their ticket.", True),
        ]

        for name, description, is_mod_only in commands_info:
            embed.add_field(
                name=f"/{name}",
                value=f"{description} {'(Mod/Admin only)' if is_mod_only else ''}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

# Assign the unverified role upon member join
@bot.event
async def on_member_join(member):
    print(f'{member} joined the server.')
    unverified_role = member.guild.get_role(UNVERIFIED_ROLE_ID)
    if unverified_role:
        try:
            await member.add_roles(unverified_role)
            print(f"Assigned role '{unverified_role.name}' to {member.name}.")
        except discord.Forbidden:
            print("Bot does not have permission to assign roles.")
        except discord.HTTPException as e:
            print(f"Failed to assign role: {e}")
    else:
        print(f"Role not found with ID {UNVERIFIED_ROLE_ID}.")

# Event listener for role updates
@bot.event
async def on_member_update(before, after):
    guild = after.guild
    verified_role = guild.get_role(VERIFIED_ROLE_ID)
    unverified_role = guild.get_role(UNVERIFIED_ROLE_ID)

    if verified_role is None or unverified_role is None:
        print("Verified or unverified role not found.")
        return

    # If member gains the verified role
    if verified_role not in before.roles and verified_role in after.roles:
        if unverified_role in after.roles:
            try:
                await after.remove_roles(unverified_role)
                print(f"Removed unverified role from {after.name} (gained verified role).")
            except discord.Forbidden:
                print(f"Permission error when removing role from {after.name}.")
            except discord.HTTPException as e:
                print(f"Failed to remove role from {after.name}: {e}")

    # If member loses the verified role
    elif verified_role in before.roles and verified_role not in after.roles:
        if unverified_role not in after.roles:
            try:
                await after.add_roles(unverified_role)
                print(f"Added unverified role to {after.name} (lost verified role).")
            except discord.Forbidden:
                print(f"Permission error when adding role to {after.name}.")
            except discord.HTTPException as e:
                print(f"Failed to add role to {after.name}: {e}")

# Periodic role consistency check
@tasks.loop(minutes=10)
async def role_consistency_check():
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print("Guild not found.")
        return

    verified_role = guild.get_role(VERIFIED_ROLE_ID)
    unverified_role = guild.get_role(UNVERIFIED_ROLE_ID)

    if verified_role is None or unverified_role is None:
        print("Verified or unverified role not found.")
        return

    for member in guild.members:
        if verified_role in member.roles and unverified_role in member.roles:
            try:
                await member.remove_roles(unverified_role)
                print(f"Removed unverified role from {member.name}.")
            except discord.Forbidden:
                print(f"Permission error when removing role from {member.name}.")
            except discord.HTTPException as e:
                print(f"Failed to remove role from {member.name}: {e}")
        elif verified_role not in member.roles and unverified_role not in member.roles:
            try:
                await member.add_roles(unverified_role)
                print(f"Added unverified role to {member.name}.")
            except discord.Forbidden:
                print(f"Permission error when adding role to {member.name}.")
            except discord.HTTPException as e:
                print(f"Failed to add role from {member.name}: {e}")

# Ticket Button View
class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Create Ticket",
        style=discord.ButtonStyle.green,
        custom_id="create_ticket_button"
    )
    async def create_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        guild = interaction.guild
        user = interaction.user

        # Check if the user already has an open ticket
        existing_channel = discord.utils.get(
            guild.text_channels,
            topic=f"Ticket opened by {user.id}"
        )
        if existing_channel:
            await interaction.response.send_message(
                f"You already have an open ticket: {existing_channel.mention}",
                ephemeral=True
            )
            return

        # Get the next ticket number
        ticket_number = await self.get_next_ticket_number()

        # Define permissions for the new channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            )
        }

        # Get roles for mods/admins
        mod_role = discord.utils.get(guild.roles, name=MOD_ROLE_NAME)
        admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)

        # Add mods and admins to overwrites
        if mod_role:
            overwrites[mod_role] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            )
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            )

        # Get or create the category for tickets
        category = discord.utils.get(guild.categories, name="Tickets")
        if category is None:
            category = await guild.create_category("Tickets")

        # Create the ticket channel with the ticket number
        channel_name = f"ticket-{ticket_number}"
        channel = await guild.create_text_channel(
            channel_name,
            overwrites=overwrites,
            category=category,
            topic=f"Ticket opened by {user.id}"
        )

        # Send a message in the ticket channel mentioning the user and staff roles
        staff_roles = []
        if mod_role:
            staff_roles.append(mod_role.mention)
        if admin_role:
            staff_roles.append(admin_role.mention)
        staff_mentions = ' '.join(staff_roles)

        await channel.send(
            f"{user.mention} has created a ticket. {staff_mentions}, please assist.\n\nPlease answer the following questions:\n\n1. [Question 1]\n\n2. [Question 2]\n\n3. [Question 3]"
        )

        await interaction.response.send_message(
            f"Ticket created: {channel.mention}", ephemeral=True
        )

    async def get_next_ticket_number(self):
        # Path to the ticket number file
        file_path = 'ticket_number.txt'

        # Check if the file exists
        if not os.path.exists(file_path):
            # Create the file and initialize the ticket number to 1
            async with aiofiles.open(file_path, mode='w') as f:
                await f.write('1')
            return 1

        # Read the last ticket number
        async with aiofiles.open(file_path, mode='r') as f:
            content = await f.read()
            ticket_number = int(content.strip())

        # Increment the ticket number
        ticket_number += 1

        # Write the new ticket number back to the file
        async with aiofiles.open(file_path, mode='w') as f:
            await f.write(str(ticket_number))

        return ticket_number

# Ensure the ticket button is present in the specified channel
async def ensure_ticket_button():
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {TICKET_CHANNEL_ID} not found.")
        return

    if TICKET_BUTTON_MESSAGE_ID != 123456789012345678:
        try:
            # Try to fetch the message with the given ID
            message = await channel.fetch_message(TICKET_BUTTON_MESSAGE_ID)
            if message.author.id == bot.user.id:
                print("Ticket button already exists in the channel.")
                return
        except discord.NotFound:
            # Message not found, we need to send a new one
            print("Ticket button message not found. Creating a new one.")
    else:
        print("Ticket button message ID not set. Creating a new one.")

    # Send the new button message
    view = TicketButton()
    message = await channel.send("Click the button below to create a ticket.", view=view)
    await message.pin()
    print(f"Ticket button has been sent to the channel. Message ID: {message.id}")
    print("Please update TICKET_BUTTON_MESSAGE_ID in your code with the above message ID.")

# Ticket System Cog
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# Verification Commands Cog
class VerificationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="verify_user",
        description="Verify a user by assigning roles and closing their ticket."
    )
    @app_commands.describe(member="The member to verify")
    async def verify_user(
        self, interaction: discord.Interaction, member: discord.Member
    ):
        # Check if the user has the required role
        mod_role = discord.utils.get(interaction.guild.roles, name=MOD_ROLE_NAME)
        admin_role = discord.utils.get(interaction.guild.roles, name=ADMIN_ROLE_NAME)

        if mod_role not in interaction.user.roles and admin_role not in interaction.user.roles:
            await interaction.response.send_message(
                "You do not have permission to use this command.", ephemeral=True
            )
            return

        # Get the roles
        verified_role = interaction.guild.get_role(VERIFIED_ROLE_ID)
        unverified_role = interaction.guild.get_role(UNVERIFIED_ROLE_ID)

        if verified_role is None:
            await interaction.response.send_message(
                "Verified role not found.", ephemeral=True
            )
            return

        # Remove the unverified role
        if unverified_role in member.roles:
            await member.remove_roles(unverified_role)

        # Add the verified role
        await member.add_roles(verified_role)

        # Prepare the response message
        deletion_message = f"{member.mention} has been verified."

        # Send the interaction response before deleting the channel
        await interaction.response.send_message(
            deletion_message, ephemeral=False
        )

        # Delete the user's ticket channel
        ticket_channel = discord.utils.get(
            interaction.guild.text_channels,
            topic=f"Ticket opened by {member.id}"
        )
        if ticket_channel:
            try:
                await ticket_channel.delete()
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                pass

# Moderation Commands Cog
class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ban_role",
        description="Ban all members with a specific role."
    )
    @app_commands.describe(role="The role whose members will be banned")
    async def ban_role(
        self, interaction: discord.Interaction, role: discord.Role
    ):
        # Check if the user has the required role
        mod_role = discord.utils.get(interaction.guild.roles, name=MOD_ROLE_NAME)
        admin_role = discord.utils.get(interaction.guild.roles, name=ADMIN_ROLE_NAME)

        if mod_role not in interaction.user.roles and admin_role not in interaction.user.roles:
            await interaction.response.send_message(
                "You do not have permission to use this command.", ephemeral=True
            )
            return

        # Get members with the specified role
        members_to_ban = [member for member in role.members if not member.bot]

        if not members_to_ban:
            await interaction.response.send_message(
                f"No members found with the role {role.name}.", ephemeral=True
            )
            return

        # Confirmation view
        class ConfirmBanView(discord.ui.View):
            def __init__(self, members):
                super().__init__(timeout=60)
                self.members = members

            @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                if interaction_button.user != interaction.user:
                    await interaction_button.response.send_message("You cannot confirm this action.", ephemeral=True)
                    return

                await interaction_button.response.defer()
                for member in self.members:
                    try:
                        await member.ban(reason=f"Banned by {interaction.user} using /ban_role command.")
                        logging.info(f"Banned {member} (ID: {member.id})")
                    except Exception as e:
                        logging.error(f"Failed to ban {member} (ID: {member.id}): {e}")

                await interaction.followup.send(f"Banned {len(self.members)} members with the role {role.name}.")
                self.stop()

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
            async def cancel(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                if interaction_button.user != interaction.user:
                    await interaction_button.response.send_message("You cannot cancel this action.", ephemeral=True)
                    return

                await interaction_button.response.send_message("Ban operation canceled.", ephemeral=True)
                self.stop()

        view = ConfirmBanView(members_to_ban)
        await interaction.response.send_message(
            f"Are you sure you want to ban {len(members_to_ban)} members with the role {role.name}?",
            view=view,
            ephemeral=True
        )

    @app_commands.command(
        name="kick_role",
        description="Kick all members with a specific role."
    )
    @app_commands.describe(role="The role whose members will be kicked")
    async def kick_role(
        self, interaction: discord.Interaction, role: discord.Role
    ):
        # Similar implementation to ban_role, replace ban with kick

        # Check if the user has the required role
        mod_role = discord.utils.get(interaction.guild.roles, name=MOD_ROLE_NAME)
        admin_role = discord.utils.get(interaction.guild.roles, name=ADMIN_ROLE_NAME)

        if mod_role not in interaction.user.roles and admin_role not in interaction.user.roles:
            await interaction.response.send_message(
                "You do not have permission to use this command.", ephemeral=True
            )
            return

        # Get members with the specified role
        members_to_kick = [member for member in role.members if not member.bot]

        if not members_to_kick:
            await interaction.response.send_message(
                f"No members found with the role {role.name}.", ephemeral=True
            )
            return

        # Confirmation view
        class ConfirmKickView(discord.ui.View):
            def __init__(self, members):
                super().__init__(timeout=60)
                self.members = members

            @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                if interaction_button.user != interaction.user:
                    await interaction_button.response.send_message("You cannot confirm this action.", ephemeral=True)
                    return

                await interaction_button.response.defer()
                for member in self.members:
                    try:
                        await member.kick(reason=f"Kicked by {interaction.user} using /kick_role command.")
                        logging.info(f"Kicked {member} (ID: {member.id})")
                    except Exception as e:
                        logging.error(f"Failed to kick {member} (ID: {member.id}): {e}")

                await interaction.followup.send(f"Kicked {len(self.members)} members with the role {role.name}.")
                self.stop()

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
            async def cancel(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                if interaction_button.user != interaction.user:
                    await interaction_button.response.send_message("You cannot cancel this action.", ephemeral=True)
                    return

                await interaction_button.response.send_message("Kick operation canceled.", ephemeral=True)
                self.stop()

        view = ConfirmKickView(members_to_kick)
        await interaction.response.send_message(
            f"Are you sure you want to kick {len(members_to_kick)} members with the role {role.name}?",
            view=view,
            ephemeral=True
        )

# Setup function to add cogs
async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
    await bot.add_cog(TicketSystem(bot))
    await bot.add_cog(VerificationCommands(bot))
    await bot.add_cog(ModerationCommands(bot))

# On ready event
@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')
    bot.add_view(TicketButton())
    await ensure_ticket_button()
    await load_extensions()
    await setup(bot)
    await bot.tree.sync()
    logging.info("Bot is ready and slash commands have been synced.")
    role_consistency_check.start()

# Run the bot
bot.run(BOT_TOKEN)
