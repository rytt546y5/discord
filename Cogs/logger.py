import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = “logger_config.json”

def load_data():
if not os.path.exists(DATA_FILE):
return {}

with open(DATA_FILE, "r", encoding="utf-8") as f:
    return json.load(f)

def save_data(data):
with open(DATA_FILE, “w”, encoding=“utf-8”) as f:
json.dump(data, f, ensure_ascii=False, indent=4)

class Logger(commands.Cog):
def init(self, bot):
self.bot = bot

@app_commands.command(
    name="logger",
    description="参加・退出ログチャンネルを設定します"
)
@app_commands.default_permissions(administrator=True)
async def logger(
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
        title="📥 メンバー参加",
        color=discord.Color.green()
    )
    embed.add_field(
        name="ユーザー",
        value=f"{member.mention}\n{member} ({member.id})",
        inline=False
    )
    embed.add_field(
        name="アカウント作成日",
        value=discord.utils.format_dt(
            member.created_at,
            style="F"
        ),
        inline=False
    )
    embed.set_thumbnail(
        url=member.display_avatar.url
    )
    embed.set_footer(
        text=f"Member Count: {member.guild.member_count}"
    )
    try:
        await channel.send(embed=embed)
    except Exception:
        pass
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
        title="📤 メンバー退出",
        color=discord.Color.red()
    )
    embed.add_field(
        name="ユーザー",
        value=f"{member}\nID: {member.id}",
        inline=False
    )
    embed.set_thumbnail(
        url=member.display_avatar.url
    )
    embed.set_footer(
        text=f"Member Count: {member.guild.member_count}"
    )
    try:
        await channel.send(embed=embed)
    except Exception:
        pass

async def setup(bot):
await bot.add_cog(Logger(bot))
