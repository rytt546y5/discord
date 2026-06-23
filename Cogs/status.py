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
# VIEW① 表示用
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
            description=f"{STATUS_EMOJI.get(s.get('status'))} 現在の状態",
            color=discord.Color.gold()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# =====================
# VIEW② 管理用（変更）
# =====================

class StatusSelect(discord.ui.Select):
    def __init__(self):

        options = [
            discord.SelectOption(label="対応可能", value="green", emoji="🟢"),
            discord.SelectOption(label="対応遅延", value="yellow", emoji="🟡"),
            discord.SelectOption(label="対応不可", value="red", emoji="🔴"),
        ]

        super().__init__(
            placeholder="ステータスを変更",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        data = load()
        gid = str(interaction.guild.id)

        data[gid] = {
            "status": self.values[0]
        }

        save(data)

        await interaction.response.send_message(
            f"✅ 更新: {self.values[0]}",
            ephemeral=True
        )


class StatusAdminView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StatusSelect())


# =====================
# COG
# =====================

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # 表示パネル
    # =====================

    @app_commands.command(
        name="status_panel",
        description="ユーザー向けステータスパネル設置"
    )
    async def status_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        embed = discord.Embed(
            title="📌 ステータスパネル",
            description="🔍 ボタンで現在の状態を確認できます",
            color=discord.Color.blurple()
        )

        await channel.send(
            embed=embed,
            view=StatusView()
        )

        await interaction.response.send_message(
            "✅ 表示パネル設置完了",
            ephemeral=True
        )

    # =====================
    # 管理パネル
    # =====================

    @app_commands.command(
        name="status_admin",
        description="管理者用ステータス変更パネル"
    )
    @app_commands.default_permissions(administrator=True)
    async def status_admin(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        embed = discord.Embed(
            title="🛠 ステータス管理",
            description="ここからステータスを変更できます",
            color=discord.Color.red()
        )

        await channel.send(
            embed=embed,
            view=StatusAdminView()
        )

        await interaction.response.send_message(
            "✅ 管理パネル設置完了",
            ephemeral=True
        )


# =====================
# SETUP
# =====================

async def setup(bot):
    await bot.add_cog(Status(bot))
    bot.add_view(StatusView())
    bot.add_view(StatusAdminView())
