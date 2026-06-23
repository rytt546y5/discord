import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random

DATA_FILE = “giveaway.json”

=====================

DATA

=====================

def load_data():
if not os.path.exists(DATA_FILE):
return {}

with open(DATA_FILE, "r", encoding="utf-8") as f:
    return json.load(f)

def save_data(data):
with open(DATA_FILE, “w”, encoding=“utf-8”) as f:
json.dump(
data,
f,
indent=2,
ensure_ascii=False
)

=====================

VIEW

=====================

class GiveawayView(discord.ui.View):
def init(self):
super().init(timeout=None)

@discord.ui.button(
    label="🎉 参加する",
    style=discord.ButtonStyle.green,
    custom_id="giveaway_join"
)
async def join(
    self,
    interaction: discord.Interaction,
    button: discord.ui.Button
):
    data = load_data()
    giveaway_id = str(interaction.message.id)
    if giveaway_id not in data:
        data[giveaway_id] = []
    if interaction.user.id in data[giveaway_id]:
        return await interaction.response.send_message(
            "⚠️ すでに参加済みです",
            ephemeral=True
        )
    data[giveaway_id].append(
        interaction.user.id
    )
    save_data(data)
    await interaction.response.send_message(
        "✅ 抽選に参加しました",
        ephemeral=True
    )

=====================

COG

=====================

class Giveaway(commands.Cog):
def init(self, bot):
self.bot = bot

# =====================
# パネル設置
# =====================
@app_commands.command(
    name="giveaway_panel",
    description="抽選イベントパネル設置"
)
@app_commands.describe(
    channel="設置チャンネル",
    title="タイトル",
    description="説明文",
    image="画像（任意）"
)
async def giveaway_panel(
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
        color=discord.Color.gold()
    )
    if image:
        embed.set_image(
            url=image.url
        )
    embed.add_field(
        name="🎉 参加方法",
        value="下のボタンを押すだけで参加できます",
        inline=False
    )
    msg = await channel.send(
        embed=embed,
        view=GiveawayView()
    )
    data = load_data()
    data[str(msg.id)] = []
    save_data(data)
    await interaction.response.send_message(
        f"✅ giveaway設置完了\n\nメッセージID: `{msg.id}`",
        ephemeral=True
    )
# =====================
# 抽選
# =====================
@app_commands.command(
    name="giveaway_pick",
    description="当選者を選出"
)
@app_commands.describe(
    message_id="抽選パネルのメッセージID"
)
async def giveaway_pick(
    self,
    interaction: discord.Interaction,
    message_id: str
):
    data = load_data()
    users = data.get(message_id)
    if not users:
        return await interaction.response.send_message(
            "❌ 参加者がいません",
            ephemeral=True
        )
    winner_id = random.choice(users)
    await interaction.response.send_message(
        f"🎉 当選者\n\n<@{winner_id}>"
    )

=====================

SETUP

=====================

async def setup(bot):
await bot.add_cog(
Giveaway(bot)
)
