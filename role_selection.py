import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# --- Configuration Values ---
ROLES_FILE = "roles.json"  # Path to the roles file

# --- End of Configuration Values ---

class RoleSelection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.roles_file = ROLES_FILE
        self.roles_data = self.load_roles()

    def load_roles(self):
        if os.path.exists(self.roles_file):
            with open(self.roles_file, "r") as file:
                data = json.load(file)
                if "questions" not in data:
                    data["questions"] = []
                return data
        return {"questions": []}

    def save_roles(self):
        with open(self.roles_file, "w") as file:
            json.dump(self.roles_data, file, indent=4)

    def is_moderator_or_admin():
        async def predicate(interaction: discord.Interaction) -> bool:
            return interaction.user.guild_permissions.manage_roles or interaction.user.guild_permissions.administrator
        return app_commands.check(predicate)

    @app_commands.command(
        name="set_roles",
        description="Set roles and associated question."
    )
    @app_commands.describe(
        question="The question to ask for role selection",
        role1="First role",
        role2="Second role",
        role3="Third role (optional)",
        role4="Fourth role (optional)",
        role5="Fifth role (optional)",
        role6="Sixth role (optional)"
    )
    @is_moderator_or_admin()
    async def set_roles(
        self,
        interaction: discord.Interaction,
        question: str,
        role1: discord.Role,
        role2: discord.Role,
        role3: discord.Role = None,
        role4: discord.Role = None,
        role5: discord.Role = None,
        role6: discord.Role = None
    ):
        roles = [role for role in [role1, role2, role3, role4, role5, role6] if role]
        role_data = [{"id": role.id, "name": role.name} for role in roles]

        self.roles_data["questions"].append({
            "question": question,
            "roles": role_data
        })
        self.save_roles()
        await interaction.response.send_message(
            f"Roles and question have been set.", ephemeral=True
        )

    @app_commands.command(
        name="list_questions",
        description="List all set questions."
    )
    async def list_questions(self, interaction: discord.Interaction):
        if not self.roles_data["questions"]:
            await interaction.response.send_message(
                "No questions have been set.", ephemeral=True
            )
            return

        message = "Current questions:\n"
        for i, q in enumerate(self.roles_data["questions"]):
            message += f"{i + 1}: {q['question']} - Roles: {', '.join([role['name'] for role in q['roles']])}\n"

        await interaction.response.send_message(message, ephemeral=True)

    @app_commands.command(
        name="remove_question",
        description="Remove a specific question by number."
    )
    @app_commands.describe(question_number="The number of the question to remove")
    @is_moderator_or_admin()
    async def remove_question(
        self,
        interaction: discord.Interaction,
        question_number: int
    ):
        if not self.roles_data["questions"]:
            await interaction.response.send_message(
                "No questions have been set.", ephemeral=True
            )
            return

        if question_number < 1 or question_number > len(self.roles_data["questions"]):
            await interaction.response.send_message(
                "Invalid question number.", ephemeral=True
            )
            return

        removed_question = self.roles_data["questions"].pop(question_number - 1)
        self.save_roles()
        await interaction.response.send_message(
            f"Removed question: {removed_question['question']}", ephemeral=True
        )

    @app_commands.command(
        name="pick_role",
        description="Pick a role based on a question."
    )
    async def pick_role(self, interaction: discord.Interaction):
        if not self.roles_data["questions"]:
            await interaction.response.send_message(
                "Roles have not been set yet.", ephemeral=True
            )
            return

        # Present a list of questions to choose from
        question_options = [
            discord.SelectOption(label=q["question"], value=str(i))
            for i, q in enumerate(self.roles_data["questions"])
        ]

        class QuestionSelect(discord.ui.Select):
            def __init__(self, bot, options):
                self.bot = bot
                super().__init__(placeholder="Choose a question...", options=options)

            async def callback(self, interaction: discord.Interaction):
                selected_index = int(self.values[0])
                question_data = self.bot.cogs["RoleSelection"].roles_data["questions"][selected_index]
                question = question_data["question"]
                roles = question_data["roles"]

                role_options = [
                    discord.SelectOption(label=role["name"], value=str(role["id"]))
                    for role in roles
                ]

                class RoleSelect(discord.ui.Select):
                    def __init__(self, bot, options):
                        self.bot = bot
                        super().__init__(placeholder="Choose your role...", options=options)

                    async def callback(self, interaction: discord.Interaction):
                        role_id = int(self.values[0])
                        role = interaction.guild.get_role(role_id)
                        if role:
                            await interaction.user.add_roles(role)
                            await interaction.response.send_message(
                                f"You have been given the '{role.name}' role.",
                                ephemeral=True
                            )

                view = discord.ui.View()
                view.add_item(RoleSelect(self.bot, role_options))
                await interaction.response.send_message(
                    content=question, view=view, ephemeral=True
                )

        view = discord.ui.View()
        view.add_item(QuestionSelect(self.bot, question_options))
        await interaction.response.send_message(
            content="Select a question to answer:", view=view, ephemeral=True
        )

    @app_commands.command(
        name="remove_role",
        description="Remove a role."
    )
    async def remove_role(self, interaction: discord.Interaction):
        user_roles = interaction.user.roles
        options = [
            discord.SelectOption(label=role.name, value=str(role.id))
            for role in user_roles if role.id != interaction.guild.id
        ]

        if not options:
            await interaction.response.send_message(
                "You have no roles to remove.", ephemeral=True
            )
            return

        class RoleRemoveSelect(discord.ui.Select):
            def __init__(self, bot, options):
                self.bot = bot
                super().__init__(placeholder="Choose a role to remove...", options=options)

            async def callback(self, interaction: discord.Interaction):
                role_id = int(self.values[0])
                role = interaction.guild.get_role(role_id)
                if role:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message(
                        f"The '{role.name}' role has been removed.", ephemeral=True
                    )

        view = discord.ui.View()
        view.add_item(RoleRemoveSelect(self.bot, options))
        await interaction.response.send_message(
            content="Select a role to remove:", view=view, ephemeral=True
        )

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user}')

async def setup(bot):
    await bot.add_cog(RoleSelection(bot))
