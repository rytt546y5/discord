import discord
from discord import app_commands
from discord.ext import commands

class Nuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="nuke", description="チャンネルのメッセージログを削除します")
    @app_commands.default_permissions(manage_channels=True)
    async def nuke_channel_command(self, interaction: discord.Interaction):
        try:
            new_channel = await interaction.channel.clone()

            await new_channel.edit(position=interaction.channel.position)

            await interaction.channel.delete()

            embed = discord.Embed(title="Nuke", description=f"{interaction.user.mention}がチャンネルのメッセージログを削除しました", color=discord.Color.green())

            await new_channel.send(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="チャンネルを削除する権限がありません。\nBotの権限を確認してください。", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Nuke(bot))
