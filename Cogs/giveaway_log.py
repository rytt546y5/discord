import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "data.json"

# =====================
# DATA MANAGEMENT
# =====================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"config": {}, "panels": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"config": {}, "panels": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =====================
# VIEWS (BUTTONS)
# =====================

class BaseReceiveView(discord.ui.View):
    """ギフトとリワード共通のボタン処理クラス"""
    def __init__(self, custom_id: str):
        super().__init__(timeout=None)
        self.custom_id = custom_id

    async def handle_receive(self, interaction: discord.Interaction, panel_type: str):
        data = load_data()
        msg_id = str(interaction.message.id)
        guild_id = str(interaction.guild.id)

        # パネル情報の取得
        panel_info = data.get("panels", {}).get(msg_id)
        if not panel_info:
            return await interaction.response.send_message("❌ このパネルのデータが見つかりません。", ephemeral=True)

        # 重複チェック
        if interaction.user.id in panel_info.get("recipients", []):
            return await interaction.response.send_message("❌ すでに受け取り済みです。", ephemeral=True)

        # ログチャンネルの取得
        log_key = "gift_log_id" if panel_type == "gift" else "reward_log_id"
        log_channel_id = data.get("config", {}).get(guild_id, {}).get(log_key)
        
        try:
            log_channel = await interaction.guild.fetch_channel(log_channel_id)
        except:
            return await interaction.response.send_message("❌ ログチャンネルが設定されていないか、見つかりません。", ephemeral=True)

        # データの更新と保存
        panel_info.setdefault("recipients", []).append(interaction.user.id)
        save_data(data)

        # ログ送信
        embed = discord.Embed(
            title=f"🎁 {'配布' if panel_type == 'gift' else '報酬'}受取ログ",
            color=discord.Color.gold() if panel_type == "gift" else discord.Color.blue()
        )
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 ユーザー", value=interaction.user.mention, inline=True)
        embed.add_field(name="📦 商品", value=panel_info['product_name'], inline=True)
        
        await log_channel.send(embed=embed)
        await interaction.response.send_message(f"✅ **{panel_info['product_name']}** を受け取りました！", ephemeral=True)

class GiftView(BaseReceiveView):
    def __init__(self):
        super().__init__(custom_id="gift_receive_button")

    @discord.ui.button(label="🎁 ギフトを受け取る", style=discord.ButtonStyle.green, custom_id="gift_receive_button")
    async def receive(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_receive(interaction, "gift")

class RewardView(BaseReceiveView):
    def __init__(self):
        super().__init__(custom_id="reward_receive_button")

    @discord.ui.button(label="💰 報酬を受け取る", style=discord.ButtonStyle.blurple, custom_id="reward_receive_button")
    async def receive(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_receive(interaction, "reward")

# =====================
# BOT CLASS
# =====================

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # 永続Viewの登録（これをしないと再起動後にボタンが動かない）
        self.add_view(GiftView())
        self.add_view(RewardView())
        await self.tree.sync()

bot = MyBot()

# =====================
# COMMANDS
# =====================

@bot.tree.command(name="setup_logs", description="ログチャンネルを一括設定します")
@app_commands.describe(gift_log="ギフト用のログチャンネル", reward_log="リワード用のログチャンネル")
async def setup_logs(interaction: discord.Interaction, gift_log: discord.TextChannel, reward_log: discord.TextChannel):
    data = load_data()
    gid = str(interaction.guild.id)
    
    if gid not in data["config"]:
        data["config"][gid] = {}
    
    data["config"][gid]["gift_log_id"] = gift_log.id
    data["config"][gid]["reward_log_id"] = reward_log.id
    save_data(data)
    
    await interaction.response.send_message(f"✅ 設定完了しました。\nギフトログ: {gift_log.mention}\n報酬ログ: {reward_log.mention}", ephemeral=True)

@bot.tree.command(name="gift_panel", description="配布パネルを設置します")
async def gift_panel(interaction: discord.Interaction, channel: discord.TextChannel, product_name: str, image: discord.Attachment = None):
    data = load_data()
    if not data["config"].get(str(interaction.guild.id), {}).get("gift_log_id"):
        return await interaction.response.send_message("❌ 先に `/setup_logs` でログ設定をしてください。", ephemeral=True)

    embed = discord.Embed(title="🎁 ギフト配布", description=f"商品: **{product_name}**\n下のボタンを押して受け取ってください。", color=discord.Color.green())
    if image: embed.set_image(url=image.url)

    msg = await channel.send(embed=embed, view=GiftView())
    
    # パネル情報を保存
    data["panels"][str(msg.id)] = {"product_name": product_name, "type": "gift", "recipients": []}
    save_data(data)
    
    await interaction.response.send_message("✅ ギフトパネルを設置しました。", ephemeral=True)

@bot.tree.command(name="reward_panel", description="報酬パネルを設置します")
async def reward_panel(interaction: discord.Interaction, channel: discord.TextChannel, product_name: str, image: discord.Attachment = None):
    data = load_data()
    if not data["config"].get(str(interaction.guild.id), {}).get("reward_log_id"):
        return await interaction.response.send_message("❌ 先に `/setup_logs` でログ設定をしてください。", ephemeral=True)

    embed = discord.Embed(title="💰 報酬受取", description=f"内容: **{product_name}**\n下のボタンを押して受け取ってください。", color=discord.Color.blue())
    if image: embed.set_image(url=image.url)

    msg = await channel.send(embed=embed, view=RewardView())
    
    # パネル情報を保存
    data["panels"][str(msg.id)] = {"product_name": product_name, "type": "reward", "recipients": []}
    save_data(data)
    
    await interaction.response.send_message("✅ 報酬パネルを設置しました。", ephemeral=True)

# 実行
# bot.run("YOUR_TOKEN_HERE")
