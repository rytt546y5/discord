import discord
from discord import app_commands
from discord.ext import commands
import json
import os

CONFIG_FILE = 'data/join_log_config.json'

class JoinLogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self._load_config()

    def _load_config(self):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_config(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    @app_commands.command(name="join_log", description="入室ログを送信するチャンネルを設定します")
    @app_commands.describe(channel="入室ログを送信するチャンネル")
    @app_commands.default_permissions(administrator=True)
    async def set_join_log(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild_id)
        self.config[guild_id] = channel.id
        self._save_config()
        await interaction.response.send_message(f"入室ログの送信先を {channel.mention} に設定しました。",ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        channel_id = self.config.get(guild_id)
        if channel_id is None:
            return

        channel = member.guild.get_channel(channel_id)
        if channel is None:
            return

        account_created = discord.utils.format_dt(member.created_at, style='R')
        embed = discord.Embed(title="メンバーが参加しました!",description=f"{member.mention} ({member})",color=0x2ecc71,timestamp=member.joined_at)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ユーザーID", value=str(member.id), inline=True)
        embed.add_field(name="アカウント作成日", value=account_created, inline=True)
        embed.add_field(name="メンバー数", value=f"{member.guild.member_count}人", inline=True)
        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(JoinLogCog(bot))
