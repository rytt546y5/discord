python
import discord
from discord import app_commands
from discord.ext import commands

class ServerInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="serverinfo", description="サーバーの情報を表示します")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        online = sum(1 for m in guild.members if m.status != discord.Status.offline)
        created = discord.utils.format_dt(guild.created_at, style='R')
        embed = discord.Embed(title=guild.name, color=0x3498db)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="管理者", value=guild.owner.mention, inline=True)
        embed.add_field(name="メンバー数", value=f"{guild.member_count} (オンライン: {online})", inline=True)
        embed.add_field(name="チャンネル数", value=f"テキスト: {len(guild.text_channels)} / ボイス: {len(guild.voice_channels)}", inline=True)
        embed.add_field(name="ロール数", value=f"{len(guild.roles)}", inline=True)
        embed.add_field(name="サーバーブースト", value=f"Lv.{guild.premium_tier} ({guild.premium_subscription_count})", inline=True)
        embed.add_field(name="作成日", value=created, inline=True)
        embed.set_footer(text=f"サーバーID: {guild.id}")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerInfoCog(bot))
