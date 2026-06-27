import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# 抽選ログ専用のデータファイル（他と混ざらないように分離）
DATA_FILE = "giveaway_log_config.json"

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

class GiveawayLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="giveaway_log_set",
        description="抽選（ギブアウェイ）の結果を送るログチャンネルを設定します"
    )
    async def log_set(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """抽選（Giveaway）専用のログ設定"""
        data = load_data()
        data[str(interaction.guild.id)] = channel.id
        save_data(data)

        await interaction.response.send_message(
            f"✅ 抽選（ギブアウェイ）ログを {channel.mention} に設定しました。\n※配布パネルのログとは別物です。",
            ephemeral=True
        )

# =====================
# ここが足りなかったためエラーが出ていました
# =====================
async def setup(bot):
    await bot.add_cog(GiveawayLog(bot))
