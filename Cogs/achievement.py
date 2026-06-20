import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "achievement_config.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def stars(n):
    return "⭐" * n + "☆" * (5 - n)


# =====================
# MODAL
# =====================
class AchievementModal(discord.ui.Modal):
    def __init__(self, log_channel_id: int):
        super().__init__(title="実績記入")
        self.log_channel_id = log_channel_id

        self.title_input = discord.ui.TextInput(label="タイトル", max_length=50)
        self.content_input = discord.ui.TextInput(label="内容", style=discord.TextStyle.paragraph, max_length=300)
        self.rating_input = discord.ui.TextInput(label="評価(1-5)", max_length=1)

        self.add_item(self.title_input)
        self.add_item(self.content_input)
        self.add_item(self.rating_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        channel = interaction.guild.get_channel(self.log_channel_id)

        if not channel:
            return await interaction.followup.send("❌ ログなし", ephemeral=True)

        try:
            rating = int(self.rating_input.value)
            if rating < 1 or rating > 5:
                raise ValueError
        except:
            return await interaction.followup.send("❌ 1〜5", ephemeral=True)

        embed = discord.Embed(title="実績", color=discord.Color.green())
        embed.add_field(name="ユーザー", value=interaction.user.mention, inline=False)
        embed.add_field(name="タイトル", value=self.title_input.value, inline=False)
        embed.add_field(name="内容", value=self.content_input.value, inline=False)
        embed.add_field(name="評価", value=stars(rating), inline=False)

        await channel.send(embed=embed)
        await interaction.followup.send("OK", ephemeral=True)


# =====================
# VIEW
# =====================
class AchievementView(discord.ui.View):
    def __init__(self, log_channel_id: int):
        super().__init__(timeout=None)
        self.log_channel_id = log_channel_id

    @discord.ui.button(label="実績記入", style=discord.ButtonStyle.green, custom_id="achievement_btn")
    async def btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AchievementModal(self.log_channel_id))


# =====================
# COG
# =====================
class Achievement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ✔ 英語コマンドに修正（重要）
    @app_commands.command(name="achievement_panel", description="実績パネル")
    async def panel(self, interaction: discord.Interaction, channel: discord.TextChannel, log: discord.TextChannel):

        data = load_data()
        data[str(interaction.guild.id)] = log.id
        save_data(data)

        embed = discord.Embed(title="実績パネル", description="ボタンで記入", color=discord.Color.blurple())

        await channel.send(embed=embed, view=AchievementView(log.id))
        await interaction.response.send_message("設置OK", ephemeral=True)

    @app_commands.command(name="achievement_log", description="ログ設定")
    async def log(self, interaction: discord.Interaction, channel: discord.TextChannel):

        data = load_data()
        data[str(interaction.guild.id)] = channel.id
        save_data(data)

        await interaction.response.send_message("ログ設定OK", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Achievement(bot))
