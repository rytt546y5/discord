import discord
from discord import app_commands
from discord.ext import commands

class MessageCountCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="count", description="チャンネルのメッセージ数をカウントします")
    async def count(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        count = 0
        async for _ in interaction.channel.history(limit=None):
            count += 1

        embed = discord.Embed(title="count", color=0x3498db)
        embed.add_field(name="メッセージ数", value=f"`{count:,}`", inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(MessageCountCog(bot))
