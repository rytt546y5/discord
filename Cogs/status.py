import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "status_data.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# =====================
# VIEW（パネル）
# =====================
class StatusView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def set_status(self, user_id: int, state: str):
        data = load_data()
        data[str(user_id)] = state
        save_data(data)

    def get_status(self, user_id: int):
        data = load_data()
        return data.get(str(user_id), "offline")

    # 🟢対応可能
    @discord.ui.button(label="🟢 対応可能", style=discord.ButtonStyle.green, custom_id="status_online")
    async def online(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.set_status(interaction.user.id, "online")

        await interaction.response.edit_message(
            embed=self.make_embed(interaction.user.id),
            view=self
        )

    # 🟡対応中
    @discord.ui.button(label="🟡 対応中", style=discord.ButtonStyle.gray, custom_id="status_busy")
    async def busy(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.set_status(interaction.user.id, "busy")

        await interaction.response.edit_message(
            embed=self.make_embed(interaction.user.id),
            view=self
        )

    # 🔴対応不可
    @discord.ui.button(label="🔴 対応不可", style=discord.ButtonStyle.red, custom_id="status_offline")
    async def offline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.set_status(interaction.user.id, "offline")

        await interaction.response.edit_message(
            embed=self.make_embed(interaction.user.id),
            view=self
        )

    # 表示
    def make_embed(self, user_id: int):
        state = self.get_status(user_id)

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

        return embed


# =====================
# COG
# =====================
class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="status",
        description="対応ステータスパネル表示"
    )
    async def status(self, interaction: discord.Interaction):

        view = StatusView()

        await interaction.response.send_message(
            embed=view.make_embed(interaction.user.id),
            view=view
        )


async def setup(bot):
    await bot.add_cog(Status(bot))
