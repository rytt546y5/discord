import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "achievement_config.json"


# =====================
# DATA
# =====================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def stars(n):
    return "⭐" * n + "☆" * (5 - n)


# =====================
# MODAL
# =====================
class AchievementModal(discord.ui.Modal):
    def __init__(self, log_channel_id: int):
        super().__init__(title="実績記入")

        self.log_channel_id = log_channel_id

        self.title_input = discord.ui.TextInput(
            label="タイトル",
            placeholder="例：購入したもの",
            max_length=50
        )

        self.content_input = discord.ui.TextInput(
            label="内容",
            placeholder="例：感想",
            style=discord.TextStyle.paragraph,
            max_length=300
        )

        self.rating_input = discord.ui.TextInput(
            label="評価（1〜5）",
            placeholder="数字で入力",
            max_length=1
        )

        self.add_item(self.title_input)
        self.add_item(self.content_input)
        self.add_item(self.rating_input)

    async def on_submit(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        channel = interaction.guild.get_channel(self.log_channel_id)

        if not channel:
            return await interaction.followup.send(
                "❌ ログチャンネルが見つかりません",
                ephemeral=True
            )

        try:
            rating = int(self.rating_input.value)

            if rating < 1 or rating > 5:
                raise ValueError

        except:
            return await interaction.followup.send(
                "❌ 評価は1〜5で入力してください",
                ephemeral=True
            )

        embed = discord.Embed(
            title="📊 実績報告",
            color=discord.Color.green()
        )

        embed.set_author(
            name=str(interaction.user),
            icon_url=interaction.user.display_avatar.url
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        embed.add_field(
            name="🏷 タイトル",
            value=self.title_input.value,
            inline=False
        )

        embed.add_field(
            name="📝 内容",
            value=self.content_input.value,
            inline=False
        )

        embed.add_field(
            name="⭐ 評価",
            value=stars(rating),
            inline=False
        )

        await channel.send(embed=embed)

        await interaction.followup.send(
            "✅ 実績を送信しました",
            ephemeral=True
        )


# =====================
# VIEW
# =====================
class AchievementView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📊 実績記入",
        style=discord.ButtonStyle.green,
        custom_id="achievement_btn"
    )
    async def btn(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = load_data()
        log_id = data.get(str(interaction.guild.id))

        if not log_id:
            return await interaction.response.send_message(
                "❌ ログチャンネル未設定です",
                ephemeral=True
            )

        await interaction.response.send_modal(
            AchievementModal(log_id)
        )


# =====================
# COG
# =====================
class Achievement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # パネル設置
    @app_commands.command(
        name="achievement_panel",
        description="実績パネルを設置します（画像対応）"
    )
    @app_commands.describe(
        channel="設置するチャンネル",
        title="パネルタイトル（例：実績報告）",
        description="説明文（例：下のボタンから報告できます）",
        image="パネル画像（任意・スマホアップロード可）"
    )
    async def panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        description: str,
        image: discord.Attachment = None
    ):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )

        if image:
            embed.set_image(url=image.url)

        await channel.send(
            embed=embed,
            view=AchievementView()
        )

        await interaction.response.send_message(
            "✅ 実績パネルを設置しました",
            ephemeral=True
        )

    # ログ設定
    @app_commands.command(
        name="achievement_log",
        description="実績ログチャンネルを設定"
    )
    async def log(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        data = load_data()
        data[str(interaction.guild.id)] = channel.id
        save_data(data)

        await interaction.response.send_message(
            "✅ ログチャンネルを設定しました",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Achievement(bot))
