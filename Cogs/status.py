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
# SELECT（状態変更）
# =====================

class StatusSelect(discord.ui.Select):
    def __init__(self):

        options = [
            discord.SelectOption(label="対応可能", value="green", emoji="🟢"),
            discord.SelectOption(label="対応遅延", value="yellow", emoji="🟡"),
            discord.SelectOption(label="対応不可", value="red", emoji="🔴"),
        ]

        super().__init__(
            placeholder="ステータスを選択してください",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="status_select"
        )

    async def callback(self, interaction: discord.Interaction):

        data = load()
        gid = str(interaction.guild.id)

        data[gid] = {
            "status": self.values[0],
            "text": self.values[0]  # 必要なら後で拡張
        }

        save(data)

        await interaction.response.send_message(
            f"✅ ステータス更新: {self.values[0]}",
            ephemeral=True
        )


class StatusSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StatusSelect())


# =====================
# VIEW（確認）
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
            description=f"{STATUS_EMOJI.get(s.get('status'), '⚪')} 現在の状況",
            color=discord.Color.gold()
        )

        # 🔥ここで「変更UI」を一緒に出す
        await interaction.response.send_message(
            embed=embed,
            view=StatusSelectView(),
            ephemeral=True
        )


# =====================
# COG
# =====================

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="status_panel",
        description="対応ステータスパネルを設置します"
    )
    async def status_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        embed = discord.Embed(
            title="📌 ステータスパネル",
            description="🔍ボタンから現在の状況を確認できます",
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


async def setup(bot):
    await bot.add_cog(Status(bot))
    bot.add_view(StatusView())
