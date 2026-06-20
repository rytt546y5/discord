import discord
from discord.ext import commands
from discord import app_commands
import json
import os


# =========================
# 📦 永続化ファイル
# =========================
DATA_FILE = "achievement_config.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def stars(n: int):
    return "⭐" * n + "☆" * (5 - n)


# =========================
# 📌 Modal
# =========================
class AchievementModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="実績記入")

        self.title_input = discord.ui.TextInput(
            label="タイトル",
            max_length=50
        )

        self.content_input = discord.ui.TextInput(
            label="内容",
            style=discord.TextStyle.paragraph,
            max_length=300
        )

        self.rating_input = discord.ui.TextInput(
            label="評価（1〜5）",
            placeholder="例: 5",
            max_length=1
        )

        self.add_item(self.title_input)
        self.add_item(self.content_input)
        self.add_item(self.rating_input)

    async def on_submit(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        # =========================
        # 📌 チャンネル取得
        # =========================
        data = load_data()
        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            return await interaction.followup.send(
                "❌ ログチャンネルが設定されていません",
                ephemeral=True
            )

        log_channel = interaction.guild.get_channel(data[guild_id])

        if log_channel is None:
            return await interaction.followup.send(
                "❌ ログチャンネルが見つかりません",
                ephemeral=True
            )

        # =========================
        # 📌 rating処理
        # =========================
        try:
            rating = int(self.rating_input.value)
            if rating < 1 or rating > 5:
                raise ValueError
        except:
            return await interaction.followup.send(
                "❌ 評価は1〜5で入力してください",
                ephemeral=True
            )

        # =========================
        # 📌 embed作成
        # =========================
        embed = discord.Embed(
            title="📊 実績報告",
            color=discord.Color.green()
        )

        embed.add_field(name="ユーザー", value=interaction.user.mention, inline=False)
        embed.add_field(name="タイトル", value=self.title_input.value, inline=False)
        embed.add_field(name="内容", value=self.content_input.value, inline=False)
        embed.add_field(name="評価", value=stars(rating), inline=False)

        # =========================
        # 📌 ログ送信
        # =========================
        await log_channel.send(embed=embed)

        await interaction.followup.send(
            "✅ 実績を送信しました",
            ephemeral=True
        )


# =========================
# 📌 View（ボタン）
# =========================
class AchievementView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="実績を記入",
        style=discord.ButtonStyle.green,
        custom_id="achievement_btn"
    )
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_modal(AchievementModal())


# =========================
# 📌 Cog本体
# =========================
class Achievement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # 📌 パネル設置
    # =========================
    @app_commands.command(
        name="実績記入パネル設置",
        description="実績パネルを設置します"
    )
    @app_commands.default_permissions(administrator=True)
    async def panel(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        panel_channel: discord.TextChannel
    ):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )

        await panel_channel.send(embed=embed, view=AchievementView())

        await interaction.response.send_message(
            "✅ 実績パネルを設置しました",
            ephemeral=True
        )

    # =========================
    # 📌 ログ設定
    # =========================
    @app_commands.command(
        name="実績ログ設定",
        description="実績の送信先チャンネルを設定します"
    )
    @app_commands.default_permissions(administrator=True)
    async def set_log(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        data = load_data()
        data[str(interaction.guild.id)] = channel.id
        save_data(data)

        await interaction.response.send_message(
            f"✅ 実績ログを {channel.mention} に設定しました",
            ephemeral=True
        )


# =========================
# 📌 setup
# =========================
async def setup(bot):
    await bot.add_cog(Achievement(bot))
