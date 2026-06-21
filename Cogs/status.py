import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "user_status.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# =====================
# STATUS PANEL
# =====================
class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="status",
        description="対応状況を表示・設定"
    )
    async def status(
        self,
        interaction: discord.Interaction,
        state: str = None
    ):
        """
        state:
        ・online = 対応可能
        ・busy = 対応中
        ・offline = 対応不可
        """

        data = load_data()

        # =====================
        # 設定モード
        # =====================
        if state:
            data[str(interaction.user.id)] = state
            save_data(data)

            return await interaction.response.send_message(
                f"✅ 状態更新: {state}",
                ephemeral=True
            )

        # =====================
        # 表示モード
        # =====================
        state = data.get(str(interaction.user.id), "offline")

        if state == "online":
            text = "🟢 対応可能"
        elif state == "busy":
            text = "🟡 対応中"
        else:
            text = "🔴 対応不可"

        embed = discord.Embed(
            title="📌 対応ステータス",
            description=text,
            color=discord.Color.blurple()
        )

        embed.set_footer(text="あなたの対応状況")

        await interaction.response.send_message(embed=embed)


# =====================
# SETUP
# =====================
async def setup(bot):
    await bot.add_cog(Status(bot))
