import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import timedelta

NGWORDS_FILE = "ngwords.json"
VIOLATIONS_FILE = "violations.json"


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class NgWordCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ngwords = load_json(NGWORDS_FILE, [])
        self.violations = load_json(VIOLATIONS_FILE, {})

    def add_violation(self, user_id: int, guild: discord.Guild):
        uid = str(user_id)
        self.violations[uid] = self.violations.get(uid, 0) + 1
        save_json(VIOLATIONS_FILE, self.violations)

        count = self.violations[uid]

        member = guild.get_member(user_id)
        if not member:
            return

        if count == 3:
            try:
                member.timeout(timedelta(minutes=10), reason="NGワード違反3回")
            except:
                pass

        if count >= 6:
            try:
                member.timeout(timedelta(weeks=1), reason="NGワード違反累積")
            except:
                pass
            self.violations[uid] = 0
            save_json(VIOLATIONS_FILE, self.violations)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return

        content = message.content.lower()

        for w in self.ngwords:
            if w.lower() in content:
                try:
                    await message.delete()
                except:
                    pass

                self.add_violation(message.author.id, message.guild)
                return

    @app_commands.command(name="ngword_add", description="NGワード追加")
    @app_commands.default_permissions(administrator=True)
    async def add(self, interaction: discord.Interaction, word: str):
        if word not in self.ngwords:
            self.ngwords.append(word)
            save_json(NGWORDS_FILE, self.ngwords)

        await interaction.response.send_message("追加しました", ephemeral=True)

    @app_commands.command(name="ngword_remove", description="NGワード削除")
    @app_commands.default_permissions(administrator=True)
    async def remove(self, interaction: discord.Interaction, word: str):
        if word in self.ngwords:
            self.ngwords.remove(word)
            save_json(NGWORDS_FILE, self.ngwords)

        await interaction.response.send_message("削除しました", ephemeral=True)

    @app_commands.command(name="ngword_list", description="NGワード一覧")
    async def list_words(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "\n".join(self.ngwords) if self.ngwords else "なし",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(NgWordCog(bot))
