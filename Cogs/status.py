import discord
from discord.ext import commands
from discord import app_commands
import json
import os

FILE = "status_data.json"


# =====================
# DATA
# =====================

def load():
    if not os.path.exists(FILE):
        return {}

    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


STATUS_EMOJI = {
    "green": "🟢",
    "yellow": "🟡",
    "red": "🔴"
}


# =====================
# COG
# =====================

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # 表示コマンド
    # =====================

    @app_commands.command(
        name="status",
        description="現在の対応ステータスを確認します"
    )
    async def status(self, interaction: discord.Interaction):

        data = load()
        gid = str(interaction.guild.id)

        if gid not in data:
            return await interaction.response.send_message(
                "❌ ステータスがまだ設定されていません",
                ephemeral=True
            )

        s = data[gid]

        status = s.get("status", "red")
        text = s.get("text", "未設定")

        embed = discord.Embed(
            title="📌 対応ステータス",
            description=f"{STATUS_EMOJI[status]} {text}",
            color=discord.Color.gold()
        )

        await interaction.response.send_message(embed=embed)

    # =====================
    # 変更コマンド
    # =====================

    @app_commands.command(
        name="status_set",
        description="対応ステータスを変更します（管理者専用）"
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        color="green / yellow / red",
        text="表示する内容"
    )
    async def status_set(
        self,
        interaction: discord.Interaction,
        color: str,
        text: str
    ):

        color = color.lower()

        if color not in ["green", "yellow", "red"]:
            return await interaction.response.send_message(
                "❌ green / yellow / red のみ使用可能です",
                ephemeral=True
            )

        data = load()
        gid = str(interaction.guild.id)

        data[gid] = {
            "status": color,
            "text": text
        }

        save(data)

        await interaction.response.send_message(
            f"✅ ステータス更新完了: {STATUS_EMOJI[color]}",
            ephemeral=True
        )


# =====================
# SETUP
# =====================

async def setup(bot):
    await bot.add_cog(Status(bot))
