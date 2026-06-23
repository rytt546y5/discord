import discord
from discord.ext import commands
from discord import app_commands
import json
import os

FILE = "status_data.json"

=====================

DATA

=====================

def load():
if not os.path.exists(FILE):
return {}

with open(FILE, "r", encoding="utf-8") as f:
    return json.load(f)

def save(data):
with open(FILE, “w”, encoding=“utf-8”) as f:
json.dump(
data,
f,
indent=2,
ensure_ascii=False
)

=====================

COG

=====================

class Status(commands.Cog):
def init(self, bot):
self.bot = bot

# =====================
# ステータス表示
# =====================
@app_commands.command(
    name="status",
    description="現在のステータスを表示"
)
async def status(
    self,
    interaction: discord.Interaction
):
    data = load()
    gid = str(interaction.guild.id)
    if gid not in data:
        return await interaction.response.send_message(
            "❌ ステータス未設定",
            ephemeral=True
        )
    s = data[gid]
    embed = discord.Embed(
        title="📌対応ステータス📌",
        color=discord.Color.gold()
    )
    embed.add_field(
        name="🟢 対応中",
        value=s.get("green", "未設定"),
        inline=False
    )
    embed.add_field(
        name="🟡 対応遅延",
        value=s.get("yellow", "未設定"),
        inline=False
    )
    embed.add_field(
        name="🔴 対応停止",
        value=s.get("red", "未設定"),
        inline=False
    )
    await interaction.response.send_message(
        embed=embed
    )
# =====================
# ステータス変更
# =====================
@app_commands.command(
    name="status_set",
    description="ステータス変更（管理者専用）"
)
@app_commands.default_permissions(
    administrator=True
)
@app_commands.describe(
    color="green / yellow / red",
    text="表示内容"
)
async def status_set(
    self,
    interaction: discord.Interaction,
    color: str,
    text: str
):
    color = color.lower()
    if color not in [
        "green",
        "yellow",
        "red"
    ]:
        return await interaction.response.send_message(
            "❌ green / yellow / red のみ使用可能",
            ephemeral=True
        )
    data = load()
    gid = str(interaction.guild.id)
    if gid not in data:
        data[gid] = {
            "green": "未設定",
            "yellow": "未設定",
            "red": "未設定"
        }
    data[gid][color] = text
    save(data)
    color_name = {
        "green": "🟢対応中",
        "yellow": "🟡対応遅延",
        "red": "🔴対応停止"
    }
    await interaction.response.send_message(
        f"✅ {color_name[color]} を更新しました",
        ephemeral=True
    )

=====================

SETUP

=====================

async def setup(bot):
await bot.add_cog(
Status(bot)
)
