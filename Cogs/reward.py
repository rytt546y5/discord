import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "distribution_data.json"

# =====================
# データ管理
# =====================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"config": {}, "panels": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {"config": {}, "panels": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =====================
# ボタン (永続的 View)
# =====================

class DistributionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # ギフト受け取りボタン
    @discord.ui.button(
        label="🎁 受け取る (ギフト)",
        style=discord.ButtonStyle.green,
        custom_id="btn_receive_gift"
    )
    async def receive_gift(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_receive(interaction, "gift")

    # リワード受け取りボタン
    @discord.ui.button(
        label="💰 受け取る (報酬)",
        style=discord.ButtonStyle.blurple,
        custom_id="btn_receive_reward"
    )
    async def receive_reward(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_receive(interaction, "reward")

    async def process_receive(self, interaction: discord.Interaction, p_type: str):
        data = load_data()
        msg_id = str(interaction.message.id)
        guild_id = str(interaction.guild.id)

        # パネルデータの確認
        panel = data.get("panels", {}).get(msg_id)
        if not panel:
            return await interaction.response.send_message("❌ このパネルのデータが記録されていません。", ephemeral=True)

        # 重複チェック
        if interaction.user.id in panel.get("claimed", []):
            return await interaction.response.send_message("❌ すでに受け取り済みです。", ephemeral=True)

        # ログ設定の取得
        config = data.get("config", {}).get(guild_id, {})
        log_channel_id = config.get(f"{p_type}_log_id")

        try:
            log_channel = await interaction.guild.fetch_channel(log_channel_id)
        except:
            return await interaction.response.send_message("❌ ログチャンネルが設定されていないか、見つかりません。 `/dist_setup` を実行してください。", ephemeral=True)

        # データの更新
        panel.setdefault("claimed", []).append(interaction.user.id)
        save_data(data)

        # ログ送信
        title = "🎁 ギフト受取ログ" if p_type == "gift" else "💰 報酬受取ログ"
        color = discord.Color.green() if p_type == "gift" else discord.Color.blue()
        
        embed = discord.Embed(title=title, color=color)
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 ユーザー", value=interaction.user.mention)
        embed.add_field(name="📦 商品内容", value=panel['product_name'])
        
        await log_channel.send(embed=embed)
        await interaction.response.send_message(f"✅ **{panel['product_name']}** を受け取りました！", ephemeral=True)

# =====================
# Cog クラス
# =====================

class Distribution(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # 永続Viewを登録（再起動対策）
        self.bot.add_view(DistributionView())

    # 設定コマンド
    @app_commands.command(name="dist_setup", description="配布と報酬のログチャンネルを個別に設定します")
    @app_commands.describe(gift_log="ギフト用のログ先", reward_log="報酬用のログ先")
    async def setup(self, interaction: discord.Interaction, gift_log: discord.TextChannel, reward_log: discord.TextChannel):
        data = load_data()
        gid = str(interaction.guild.id)
        
        if gid not in data["config"]:
            data["config"][gid] = {}
        
        data["config"][gid]["gift_log_id"] = gift_log.id
        data["config"][gid]["reward_log_id"] = reward_log.id
        save_data(data)
        
        await interaction.response.send_message(
            f"✅ 設定を保存しました。\n・ギフトログ: {gift_log.mention}\n・報酬ログ: {reward_log.mention}",
            ephemeral=True
        )

    # ギフトパネル設置
    @app_commands.command(name="gift_panel", description="ギフト配布パネルを設置します")
    async def g_panel(self, interaction: discord.Interaction, channel: discord.TextChannel, product_name: str, image: discord.Attachment = None):
        data = load_data()
        if not data["config"].get(str(interaction.guild.id), {}).get("gift_log_id"):
            return await interaction.response.send_message("❌ 先に `/dist_setup` でログ設定をしてください。", ephemeral=True)

        embed = discord.Embed(title="🎁 ギフト配布", description=f"商品: **{product_name}**", color=discord.Color.green())
        if image: embed.set_image(url=image.url)

        # ギフトボタンのみを表示するView
        view = DistributionView()
        # 不要なボタンを消す
        view.remove_item(view.receive_reward)
        
        msg = await channel.send(embed=embed, view=view)
        
        data["panels"][str(msg.id)] = {"product_name": product_name, "type": "gift", "claimed": []}
        save_data(data)
        await interaction.response.send_message("✅ ギフトパネルを設置しました。", ephemeral=True)

    # 報酬パネル設置
    @app_commands.command(name="reward_panel", description="報酬受取パネルを設置します")
    async def r_panel(self, interaction: discord.Interaction, channel: discord.TextChannel, product_name: str, image: discord.Attachment = None):
        data = load_data()
        if not data["config"].get(str(interaction.guild.id), {}).get("reward_log_id"):
            return await interaction.response.send_message("❌ 先に `/dist_setup` でログ設定をしてください。", ephemeral=True)

        embed = discord.Embed(title="💰 報酬受取", description=f"内容: **{product_name}**", color=discord.Color.blue())
        if image: embed.set_image(url=image.url)

        # リワードボタンのみを表示するView
        view = DistributionView()
        # 不要なボタンを消す
        view.remove_item(view.receive_gift)

        msg = await channel.send(embed=embed, view=view)
        
        data["panels"][str(msg.id)] = {"product_name": product_name, "type": "reward", "claimed": []}
        save_data(data)
        await interaction.response.send_message("✅ 報酬パネルを設置しました。", ephemeral=True)

# 読み込み用関数
async def setup(bot):
    await bot.add_cog(Distribution(bot))
