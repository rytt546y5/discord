import discord
from discord.ext import commands
from discord import app_commands


class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # メッセージ削除ログ
    # =====================
    @commands.Cog.listener()
    async def on_message_delete(self, message):

        if message.author.bot:
            return

        embed = discord.Embed(
            title="🗑 メッセージ削除",
            description=f"削除されたメッセージ\n```{message.content}```",
            color=discord.Color.red()
        )

        embed.set_author(
            name=str(message.author),
            icon_url=message.author.display_avatar.url
        )

        channel = discord.utils.get(
            message.guild.text_channels,
            name="log"
        )

        if channel:
            await channel.send(embed=embed)

    # =====================
    # メッセージ編集ログ
    # =====================
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):

        if before.author.bot:
            return

        embed = discord.Embed(
            title="✏ メッセージ編集",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="Before",
            value=before.content or "None",
            inline=False
        )

        embed.add_field(
            name="After",
            value=after.content or "None",
            inline=False
        )

        embed.set_author(
            name=str(before.author),
            icon_url=before.author.display_avatar.url
        )

        channel = discord.utils.get(
            before.guild.text_channels,
            name="log"
        )

        if channel:
            await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logger(bot))
