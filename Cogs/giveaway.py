import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random

# 抽選データ保存用
DATA_FILE = "giveaway_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =====================
# VIEW (参加ボタン)
# =====================

class GiveawayView(discord.ui.View):
    def __init__(self, message_id: int):
        super().__init__(timeout=None)
        self.message_id = message_id

    @discord.ui.button(
        label="🎉 参加する",
        style=discord.ButtonStyle.green,
        custom_id="giveaway_join"
    )
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        gid = str(self.message_id)

        if gid not in data:
            data[gid] = {"users": []}

        if interaction.user.id in data[gid]["users"]:
            return await interaction.response.send_message("⚠ すでに参加済みです", ephemeral=True)

        data[gid]["users"].append(interaction.user.id)
        save_data(data)

        await interaction.response.send_message("✅ 参加を受け付けました！", ephemeral=True)

# =====================
# COG (コマンド本体)
# =====================

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="giveaway_panel", description="抽選イベントパネルを設置します")
    @app_commands.describe(
        channel="パネルを設置するチャンネル",
        title="抽選のタイトル (例: 1000円分ギフト券)",
        description="抽選の説明文",
        image="パネルに表示する画像 (任意)"
    )
    async def giveaway_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        description: str,
        image: discord.Attachment = None
    ):
        # 最初にEmbedを作成
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.gold()
        )
        embed.add_field(name="🎉 参加方法", value="下のボタンを押すだけで参加できます", inline=False)
        if image:
            embed.set_image(url=image.url)

        # メッセージを送信
        msg = await channel.send(embed=embed)
        
        # IDを紐付けたViewをセット（再起動後も動くようにする）
        view = GiveawayView(msg.id)
        await msg.edit(view=view)

        # データを保存
        data = load_data()
        data[str(msg.id)] = {
            "guild_id": interaction.guild.id,
            "users": []
        }
        save_data(data)

        await interaction.response.send_message(f"✅ Giveawayを設置しました: {msg.jump_url}", ephemeral=True)

    @app_commands.command(name="giveaway_pick", description="設置済みのパネルから当選者を1名選びます")
    @app_commands.describe(message_id="抽選パネルのメッセージIDを入力してください")
    async def pick(self, interaction: discord.Interaction, message_id: str):
        data = load_data()
        panel_data = data.get(message_id)

        if not panel_data:
            return await interaction.response.send_message("❌ そのメッセージIDの抽選データが見つかりません。", ephemeral=True)

        users = panel_data.get("users", [])
        if not users:
            return await interaction.response.send_message("❌ 参加者が一人もいません。", ephemeral=True)

        # ランダム選出
        winner_id = random.choice(users)

        # 当選発表（メンション付き）
        await interaction.response.send_message(
            f"🎊 **抽選結果発表** 🎊\n当選者: <@{winner_id}>\nおめでとうございます！"
        )

# =====================
# SETUP
# =====================

async def setup(bot):
    # 保存されているすべてのパネルのViewを再起動時に登録する
    data = load_data()
    for msg_id in data.keys():
        if msg_id.isdigit():
            bot.add_view(GiveawayView(int(msg_id)))

    await bot.add_cog(Giveaway(bot))
