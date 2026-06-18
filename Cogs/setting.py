import discord
from discord.ext import commands
from discord import app_commands
from utils import load_allowed_users
import json
import os

ALLOWED_USERS_FILE = "allowed_users.json"

def save_allowed_users(ids: list[int]):
    with open(ALLOWED_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"allowed_ids": ids}, f, indent=4)

class SettingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # 許可ユーザー追加
    # -------------------------
    @app_commands.command(name="許可ユーザー追加", description="許可ユーザーリストにユーザーを追加します")
    async def add_allowed_user(self, interaction: discord.Interaction, user: discord.User):

        # Botオーナーのみ実行可
        if not await interaction.client.is_owner(interaction.user):
            return await interaction.response.send_message(
                "🚫 このコマンドはBotオーナーのみ使用できます。",
                ephemeral=True
            )

        allowed_ids = load_allowed_users()

        if user.id in allowed_ids:
            return await interaction.response.send_message(
                f"🚫 {user.mention} は既に許可されています。",
                ephemeral=True
            )

        allowed_ids.append(user.id)
        save_allowed_users(allowed_ids)

        await interaction.response.send_message(
            f"✅ {user.mention} を許可ユーザーに追加しました。",
            ephemeral=True
        )

    # -------------------------
    # 許可ユーザー削除
    # -------------------------
    @app_commands.command(name="許可ユーザー削除", description="許可ユーザーリストからユーザーを削除します")
    async def remove_allowed_user(self, interaction: discord.Interaction, user: discord.User):

        if not await interaction.client.is_owner(interaction.user):
            return await interaction.response.send_message(
                "🚫 このコマンドはBotオーナーのみ使用できます。",
                ephemeral=True
            )

        allowed_ids = load_allowed_users()

        if user.id not in allowed_ids:
            return await interaction.response.send_message(
                f"🚫 {user.mention} は許可ユーザーではありません。",
                ephemeral=True
            )

        allowed_ids.remove(user.id)
        save_allowed_users(allowed_ids)

        await interaction.response.send_message(
            f"✅ {user.mention} を許可ユーザーから削除しました。",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(SettingCog(bot))
