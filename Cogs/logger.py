import discord
from discord.ext import commands
import json
import os


DATA_FILE = "logger_config.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# =========================
# 📌 Cog
# =========================
class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # 📌 ログ設定コマンド
    # =========================
    @app_commands.command(
        name="ログ設定",
        description="ログチャンネルを設定します"
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
            f"✅ ログチャンネルを {channel.mention} に設定しました",
            ephemeral=True
        )


# =========================
# 📌 joinログ
# =========================
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        data = load_data()
        guild_id = str(member.guild.id)

        if guild_id not in data:
            return

        channel = member.guild.get_channel(data[guild_id])
        if channel is None:
            return

        embed = discord.Embed(
            title="📥 Member Join",
            description=f"{member.mention} が参加しました",
            color=discord.Color.green()
        )

        try:
            await channel.send(embed=embed)
        except:
            pass


# =========================
# 📌 leaveログ
# =========================
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):

        data = load_data()
        guild_id = str(member.guild.id)

        if guild_id not in data:
            return

        channel = member.guild.get_channel(data[guild_id])
        if channel is None:
            return

        embed = discord.Embed(
            title="📤 Member Leave",
            description=f"{member} が退出しました",
            color=discord.Color.red()
        )

        try:
            await channel.send(embed=embed)
        except:
            pass


# =========================
# setup
# =========================
async def setup(bot):
    await bot.add_cog(Logger(bot))
