import discord
from discord.ext import commands
from discord import app_commands
import json
import os

FILE = "backup.json"


def load():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # メッセージ保存
    # =====================
    @app_commands.command(
        name="message_save",
        description="チャンネルのメッセージを保存"
    )
    async def message_save(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        limit: int = 50
    ):

        await interaction.response.defer(ephemeral=True)

        messages = []
        async for msg in channel.history(limit=limit):
            messages.append({
                "author": msg.author.name,
                "content": msg.content
            })

        data = load()
        data[str(channel.id)] = messages
        save(data)

        await interaction.followup.send(
            f"✅ {len(messages)}件保存しました"
        )

    # =====================
    # 復元
    # =====================
    @app_commands.command(
        name="backup_restore",
        description="保存データを復元"
    )
    async def backup_restore(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        data = load()

        if str(channel.id) not in data:
            return await interaction.response.send_message(
                "❌ バックアップがありません",
                ephemeral=True
            )

        await interaction.response.send_message(
            "📦 復元開始",
            ephemeral=True
        )

        for msg in reversed(data[str(channel.id)]):

            embed = discord.Embed(
                description=msg["content"],
                color=discord.Color.blurple()
            )
            embed.set_footer(text=msg["author"])

            await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Backup(bot))
