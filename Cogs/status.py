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


# =====================
# VIEW（確認ボタン）
# =====================

class StatusView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔍 確認",
        style=discord.ButtonStyle.primary,
        custom_id="status_check"
    )
    async def check(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = load()
        gid = str(interaction.guild.id)

        if gid not in data:
            return await interaction.response.send_message(
                "❌ ステータス未設定",
                ephemeral=True
            )

        s = data[gid]

        embed = discord.Embed(
            title="📌 対応ステータス",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="🟢 対応可能",
            value=s.get("green", "未設定"),
            inline=False
        )

        embed.add_field(
            name="🟡 対応遅延",
            value=s.get("yellow", "未設定"),
            inline=False
        )

        embed.add_field(
            name="🔴 対応不可",
            value=s.get("red", "未設定"),
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# =====================
# COG
# =====================

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # パネル設置
    # =====================

    @app_commands.command(
        name="status_panel",
        description="対応ステータスパネルを設置します"
    )
    @app_commands.describe(
        channel="設置するチャンネル",
        green="🟢 対応可能の内容",
        yellow="🟡 対応遅延の内容",
        red="🔴 対応不可の内容"
    )
    async def status_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        green: str,
        yellow: str,
        red: str
    ):

        data = load()
        gid = str(interaction.guild.id)

        data[gid] = {
            "green": green,
            "yellow": yellow,
            "red": red
        }

        save(data)

        embed = discord.Embed(
            title="📌 ステータスパネル",
            description="下のボタンで現在の対応状況を確認できます",
            color=discord.Color.blurple()
        )

        await channel.send(
            embed=embed,
            view=StatusView()
        )

        await interaction.response.send_message(
            "✅ ステータスパネル設置完了",
            ephemeral=True
        )


# =====================
# SETUP
# =====================

async def setup(bot):
    await bot.add_cog(Status(bot))
    bot.add_view(StatusView())
