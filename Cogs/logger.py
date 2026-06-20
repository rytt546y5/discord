import discord
from discord.ext import commands
import json
import os
from datetime import datetime

DATA_FILE = "message_logs.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    # ------------------------
    # メッセージ保存
    # ------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return

        guild_id = str(message.guild.id)

        if guild_id not in self.data:
            self.data[guild_id] = {}

        self.data[guild_id][str(message.id)] = {
            "user_id": message.author.id,
            "username": str(message.author),
            "content": message.content,
            "channel_id": message.channel.id,
            "time": str(datetime.utcnow())
        }

        save_data(self.data)

    # ------------------------
    # 編集ログ
    # ------------------------
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return

        guild_id = str(before.guild.id)

        if guild_id not in self.data:
            return

        msg = self.data[guild_id].get(str(before.id))
        if msg:
            msg["edited"] = {
                "before": before.content,
                "after": after.content
            }
            save_data(self.data)

    # ------------------------
    # 削除ログ & 復元
    # ------------------------
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        guild_id = str(message.guild.id)

        if guild_id not in self.data:
            return

        msg = self.data[guild_id].get(str(message.id))
        if not msg:
            return

        channel = message.guild.system_channel

        embed = discord.Embed(
            title="🗑 メッセージ削除ログ",
            color=discord.Color.red()
        )

        embed.add_field(name="ユーザー", value=msg["username"], inline=False)
        embed.add_field(name="内容", value=msg["content"], inline=False)
        embed.add_field(name="時間", value=msg["time"], inline=False)

        if "edited" in msg:
            embed.add_field(
                name="編集履歴",
                value=f"{msg['edited']['before']} → {msg['edited']['after']}",
                inline=False
            )

        if channel:
            await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logger(bot))
