import discord
from discord import app_commands
from discord.ext import commands

class PurgeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="purge", description="指定した件数のメッセージを一括削除します")
    @app_commands.describe(count="削除するメッセージ数")
    @app_commands.default_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, count: int):
        if count < 1:
            await interaction.response.send_message("1以上の数字で指定してください。", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=count)

        await interaction.followup.send(f"{len(deleted)}件のメッセージを削除しました。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PurgeCog(bot))
