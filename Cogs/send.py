import discord
from discord.ext import commands
from discord import app_commands


class SendMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="send",
        description="指定チャンネルにメッセージ送信"
    )
    @app_commands.describe(
        channel="送信先チャンネル",
        message="送る内容"
    )
    async def send(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: str
    ):

        await channel.send(message)

        await interaction.response.send_message(
            f"✅ 送信完了 → {channel.mention}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(SendMessage(bot))
