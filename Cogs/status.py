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
# VIEW（表示）
# =====================
class StatusView(discord.ui.View):
    def __init__(self, guild_id: str):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(
        label="📌 ステータス確認",
        style=discord.ButtonStyle.primary
    )
    async def show(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = load()
        gid = str(self.guild_id)

        if gid not in data:
            return await interaction.response.send_message(
                "❌ ステータス未設定",
                ephemeral=True
            )

        s = data[gid]

        embed = discord.Embed(
            title="📌対応ステータス📌",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="🟢 対応中",
            value=s.get("green", "未設定"),
            inline=False
        )

        embed.add_field(
            name="🟡 対応遅延",
            value=s.get("yellow", "未設定"),
            inline=False
        )

        embed.add_field(
            name="🔴 対応停止",
            value=s.get("red", "未設定"),
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


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
        description="ステータス表示パネル"
    )
    async def status(self, interaction: discord.Interaction):

        view = StatusView(str(interaction.guild.id))

        embed = discord.Embed(
            title="📌対応ステータス📌",
            description="ボタンで最新ステータスを確認できます",
            color=discord.Color.gold()
        )

        await interaction.response.send_message(
            embed=embed,
            view=view
        )

    # =====================
    # 管理コマンド
    # =====================
    @app_commands.command(
        name="status_set",
        description="ステータス変更（管理者用）"
    )
    @app_commands.default_permissions(administrator=True)
    async def status_set(
        self,
        interaction: discord.Interaction,
        color: str,
        text: str
    ):

        color = color.lower()

        if color not in ["green", "yellow", "red"]:
            return await interaction.response.send_message(
                "❌ green / yellow / red のみ",
                ephemeral=True
            )

        data = load()
        gid = str(interaction.guild.id)

        if gid not in data:
            data[gid] = {
                "green": "未設定",
                "yellow": "未設定",
                "red": "未設定"
            }

        data[gid][color] = text
        save(data)

        await interaction.response.send_message(
            f"✅ 更新完了: {color} = {text}",
            ephemeral=True
        )


# =====================
# SETUP
# =====================
async def setup(bot):
    await bot.add_cog(Status(bot))
