import discord
from discord.ext import commands
import random
import json
import os
import time

# --- Configuration Values ---
VERIFIED_ROLE_ID = 123456789012345678  # Replace with your verified role ID
VERIFIED_PLUS_ROLE_ID = 123456789012345678  # Replace with your verified plus role ID

# --- End of Configuration Values ---

class FunAndLevelCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.compliments = [
            "You're an awesome friend.", "You're a gift to those around you.",
            "You're a smart cookie.", "You are awesome!",
            "You have impeccable manners.", "I like your style.",
            "You have the best laugh.", "I appreciate you.",
            "You are the most perfect you there is.", "You are enough."
        ]
        self.eight_ball_responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.",
            "Yes - definitely.", "You may rely on it.", "As I see it, yes.",
            "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.",
            "Better not tell you now.", "Cannot predict now.",
            "Concentrate and ask again.", "Don't count on it.",
            "My reply is no.", "My sources say no.", "Outlook not so good.",
            "Very doubtful."
        ]
        self.levels_file = 'levels.json'
        self.levels = self.load_levels()
        self.verified_role_id = VERIFIED_ROLE_ID
        self.verified_plus_role_id = VERIFIED_PLUS_ROLE_ID

    # Load levels from file
    def load_levels(self):
        if os.path.exists(self.levels_file):
            with open(self.levels_file, 'r') as f:
                return json.load(f)
        else:
            return {}

    # Save levels to file
    def save_levels(self):
        with open(self.levels_file, 'w') as f:
            json.dump(self.levels, f, indent=4)

    # Get XP required for next level
    def get_xp_for_next_level(self, current_level):
        return 50 * (current_level ** 2)

    # Compliment Command
    @discord.app_commands.command(
        name="compliment",
        description="Send a compliment to someone."
    )
    @discord.app_commands.describe(member="The member to compliment")
    async def compliment(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):
        compliment = random.choice(self.compliments)
        await interaction.response.send_message(
            f"{member.mention}, {compliment}"
        )

    # 8-Ball Command
    @discord.app_commands.command(
        name="eight_ball",
        description="Ask the Magic 8-Ball a question."
    )
    @discord.app_commands.describe(question="The question you want to ask the 8-Ball")
    async def eight_ball(
        self,
        interaction: discord.Interaction,
        question: str
    ):
        response = random.choice(self.eight_ball_responses)
        await interaction.response.send_message(
            f"? {question}\n**Answer:** {response}"
        )

    # Hello Command
    @discord.app_commands.command(
        name="hello",
        description="Receive a greeting from the bot."
    )
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Hello, {interaction.user.display_name}! Hope you're having a great day ?"
        )

    # Level System Methods
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        current_time = time.time()

        if user_id not in self.levels:
            self.levels[user_id] = {'xp': 0, 'level': 1, 'last_message_time': 0}

        user_data = self.levels[user_id]

        if current_time - user_data['last_message_time'] < 30:
            return

        user_data['last_message_time'] = current_time
        user_data['xp'] += 10
        xp_for_next_level = self.get_xp_for_next_level(user_data['level'])

        while user_data['xp'] >= xp_for_next_level:
            user_data['xp'] -= xp_for_next_level
            user_data['level'] += 1
            await message.channel.send(
                f"{message.author.display_name} has leveled up to level {user_data['level']}!"
            )
            await message.author.send(
                f"Congratulations! You have leveled up to level {user_data['level']}!"
            )

            if user_data['level'] == 5:
                verified_role = message.guild.get_role(self.verified_role_id)
                if verified_role:
                    await message.author.add_roles(verified_role)
                    await message.author.send(
                        f"You have been given the '{verified_role.name}' role for reaching level 5!"
                    )

            if user_data['level'] == 10:
                verified_plus_role = message.guild.get_role(self.verified_plus_role_id)
                if verified_plus_role:
                    await message.author.add_roles(verified_plus_role)
                    await message.author.send(
                        f"You have been given the '{verified_plus_role.name}' role for reaching level 10!"
                    )

            xp_for_next_level = self.get_xp_for_next_level(user_data['level'])

        self.save_levels()

    @discord.app_commands.command(
        name="level",
        description="Check your level or another person's level"
    )
    async def check_level(
        self,
        interaction: discord.Interaction,
        member: discord.Member = None
    ):
        if member is None:
            member = interaction.user

        user_id = str(member.id)
        if user_id not in self.levels:
            self.levels[user_id] = {'xp': 0, 'level': 1, 'last_message_time': 0}
            self.save_levels()

        user_data = self.levels[user_id]
        if member == interaction.user:
            await interaction.response.send_message(
                f"{member.mention}, you are currently at level {user_data['level']} with {user_data['xp']} XP."
            )
        else:
            await interaction.response.send_message(
                f"{member.display_name} is currently at level {user_data['level']} with {user_data['xp']} XP."
            )

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user}')

async def setup(bot):
    await bot.add_cog(FunAndLevelCommands(bot))
