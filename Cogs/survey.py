import discord
from discord import app_commands
from discord.ext import commands
import json
import os

SURVEY_CONFIG_FILE = "survey_config.json"

def load_config():
    if os.path.exists(SURVEY_CONFIG_FILE):
        with open(SURVEY_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(SURVEY_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# =====================
# MODAL (入力画面)
# =====================
class SurveyModal(discord.ui.Modal):
    def __init__(self, title: str):
        # モーダルのタイトル制限（45文字）
        super().__init__(title=title[:45])
        self.panel_title = title # 後でEmbedに使うために保持

    content = discord.ui.TextInput(
        label="内容を入力してください",
        style=discord.TextStyle.long,
        placeholder="具体的な要望や意見をこちらへ...",
        required=True,
        max_length=1500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        gid = str(interaction.guild.id)
        channel_id = config.get(gid, {}).get("log_channel")

        if not channel_id:
            return await interaction.response.send_message("❌ 管理者がログ送信先を設定していません。", ephemeral=True)

        channel = interaction.guild.get_channel(int(channel_id))
        if not channel:
            return await interaction.response.send_message("❌ 送信先チャンネルが見つかりませんでした。", ephemeral=True)

        # === 管理者に届くEmbed (em式) の作成 ===
        embed = discord.Embed(
            title="📥 新着アンケート受領",
            description=self.content.value,
            color=discord.Color.orange(), # 経営的に目立つオレンジ色
            timestamp=interaction.created_at
        )
        
        # 送信者の名前とアイコンをセット
        embed.set_author(
            name=f"{interaction.user.display_name} ({interaction.user.id})", 
            icon_url=interaction.user.display_avatar.url
        )
        
        # 右側の小さいアイコン（サムネイル）にもユーザーのアイコンを表示
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        # どのパネルから送られたかをフィールドに追加
        embed.add_field(name="対象パネル", value=f"**{self.panel_title}**", inline=False)
        
        embed.set_footer(text="Survey System | ユーザーからの意見")

        await channel.send(embed=embed)
        await interaction.response.send_message("✅ メッセージを送信しました。ご協力ありがとうございます！", ephemeral=True)

# =====================
# VIEW (パネルのボタン)
# =====================
class SurveyPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # 永続化

    @discord.ui.button(
        label="✍ 入力画面を開く",
        style=discord.ButtonStyle.primary,
        custom_id="survey_open_modal"
    )
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        # パネルのEmbedタイトルを取得
        panel_title = interaction.message.embeds[0].title if interaction.message.embeds else "アンケート"
        await interaction.response.send_modal(SurveyModal(title=panel_title))

# =====================
# COG (コマンド)
# =====================
class Survey(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(SurveyPanelView())

    @app_commands.command(name="survey_log_set", description="アンケートの届き先を設定します")
    @app_commands.describe(channel="回答（ログ）を送信するチャンネルを選択")
    async def survey_log_set(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config: config[gid] = {}
        config[gid]["log_channel"] = channel.id
        save_config(config)
        await interaction.response.send_message(f"✅ 届き先を {channel.mention} に設定しました。", ephemeral=True)

    @app_commands.command(name="survey_panel", description="アンケートパネルを設置します")
    @app_commands.describe(
        title="パネルのタイトル (例: 商品リクエスト)",
        description="パネルの説明文 (例: 欲しい商品があれば教えてください)"
    )
    async def survey_panel(
        self, 
        interaction: discord.Interaction, 
        title: str, 
        description: str
    ):
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text="ボタンを押すと入力画面が開きます。")
        
        await interaction.channel.send(embed=embed, view=SurveyPanelView())
        await interaction.response.send_message(f"✅ パネル「{title}」を設置しました。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Survey(bot))
