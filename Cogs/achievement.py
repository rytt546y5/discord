import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "achievement_config.json"

# =====================
# DATA SAFE
# =====================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def stars(n: int):
    n = max(1, min(5, n))
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
            placeholder="例：〇〇購入しました",
            max_length=50
        )

        self.content_input = discord.ui.TextInput(
            label="内容",
            placeholder="例：対応が早かった",
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

        try:
            # fetchではなくget_channelを使うか、なければfetch
            channel = interaction.guild.get_channel(self.log_channel_id) or await interaction.guild.fetch_channel(self.log_channel_id)
        except Exception:
            return await interaction.followup.send("❌ ログチャンネルが見つかりません", ephemeral=True)

        title = self.title_input.value.strip() or "なし"
        content = self.content_input.value.strip() or "なし"
        value = self.rating_input.value.strip()

        if not value.isdigit() or not (1 <= int(value) <= 5):
            return await interaction.followup.send("❌ 評価は1〜5の数字で入力してください", ephemeral=True)

        rating = int(value)

        embed = discord.Embed(title="📊 実績報告", color=discord.Color.green())
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="🏷 タイトル", value=title, inline=False)
        embed.add_field(name="📝 内容", value=content, inline=False)
        embed.add_field(name="⭐ 評価", value=stars(rating), inline=False)

        await channel.send(embed=embed)
        await interaction.followup.send("✅ 実績を送信しました。ご協力ありがとうございました！", ephemeral=True)

# =====================
# VIEW
# =====================

class AchievementView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # 永続化

    @discord.ui.button(
        label="📊 実績記入",
        style=discord.ButtonStyle.green,
        custom_id="achievement_btn" # 固定ID
    )
    async def btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        log_id = data.get(str(interaction.guild.id))

        if not log_id:
            return await interaction.response.send_message("❌ ログチャンネルが設定されていません。管理者に連絡してください。", ephemeral=True)

        await interaction.response.send_modal(AchievementModal(log_id))

# =====================
# COG
# =====================

class Achievement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="achievement_panel", description="実績パネルを設置します")
    @app_commands.describe(title="パネルのタイトル", description="パネルの説明文")
    @app_commands.default_permissions(administrator=True) # 管理者のみ
    async def panel(self, interaction: discord.Interaction, channel: discord.TextChannel, title: str, description: str, image: discord.Attachment = None):
        embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
        if image:
            embed.set_image(url=image.url)

        await channel.send(embed=embed, view=AchievementView())
        await interaction.response.send_message("✅ 実績パネルを設置しました。", ephemeral=True)

    @app_commands.command(name="achievement_log", description="実績の送信先チャンネルを設定します")
    @app_commands.describe(channel="実績ログを送信するチャンネル")
    @app_commands.default_permissions(administrator=True) # 管理者のみ
    async def log(self, interaction: discord.Interaction, channel: discord.TextChannel):
        data = load_data()
        data[str(interaction.guild.id)] = channel.id
        save_data(data)
        await interaction.response.send_message(f"✅ 実績の送信先を {channel.mention} に設定しました。", ephemeral=True)

# =====================
# SETUP
# =====================

async def setup(bot):
    # ここでViewを登録することで、Bot再起動後もボタンが反応するようになります
    bot.add_view(AchievementView())
    await bot.add_cog(Achievement(bot))
