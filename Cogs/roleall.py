import discord
from discord import app_commands
from discord.ext import commands

class RoleAllCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roleall_add", description="全メンバーにロールを一括付与します")
    @app_commands.describe(role="付与するロール")
    @app_commands.default_permissions(administrator=True)
    async def roleall_add(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        success = 0
        fail = 0
        for member in interaction.guild.members:
            if member.bot or role in member.roles:
                continue
            try:
                await member.add_roles(role)
                success += 1
            except discord.Forbidden:
                fail += 1

        await interaction.followup.send(f"{role.mention} を {success}人に付与しました。({fail}人は付与できませんでした...)",ephemeral=True)

    @app_commands.command(name="roleall_remove", description="全メンバーからロールを一括剥奪します")
    @app_commands.describe(role="剥奪するロール")
    @app_commands.default_permissions(administrator=True)
    async def roleall_remove(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        success = 0
        fail = 0
        for member in interaction.guild.members:
            if member.bot or role not in member.roles:
                continue
            try:
                await member.remove_roles(role)
                success += 1
            except discord.Forbidden:
                fail += 1

        await interaction.followup.send(f"{role.mention} を {success}人から剥奪しました。({fail}人は剝奪できませんでした...)",ephemeral=True)

async def setup(bot):
    await bot.add_cog(RoleAllCog(bot))
