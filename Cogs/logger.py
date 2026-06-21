import discord
from discord.ext import commands
from discord import app_commands


# =====================
# LOG VIEW
# =====================
class LoggerView(discord.ui.View):
    def __init__(self, log_channel_id: int):
        super().__init__(timeout=None)
        self.log_channel_id = log_channel_id


# =====================
# COG
# =====================
class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="set_logger",
        description="ログチャンネルを設定します"
    )
    @app_commands.default_permissions(administrator=True)
    async def set_logger(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        guild = interaction.guild

        embed = discord.Embed(
            title="📌 Logger設定",
            description=f"ログチャンネル → {channel.mention}",
            color=discord.Color.blurple()
        )

        await channel.send(embed=embed)

        await interaction.response.send_message(
            "✅ ログ設定完了",
            ephemeral=True
        )

    # =====================
    # メッセージログ
    # =====================
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild:
            return

        embed = discord.Embed(
            title="🗑 メッセージ削除",
            description=f"チャンネル: {message.channel.mention}",
            color=discord.Color.red()
        )

        embed.add_field(
            name="ユーザー",
            value=message.author.mention,
            inline=False
        )

        embed.add_field(
            name="内容",
            value=message.content if message.content else "なし",
            inline=False
        )

        await self.send_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild:
            return

        if before.content == after.content:
            return

        embed = discord.Embed(
            title="✏ メッセージ編集",
            description=f"チャンネル: {before.channel.mention}",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="Before",
            value=before.content or "なし",
            inline=False
        )

        embed.add_field(
            name="After",
            value=after.content or "なし",
            inline=False
        )

        await self.send_log(before.guild, embed)

    # =====================
    # 共通送信
    # =====================
    async def send_log(self, guild: discord.Guild, embed: discord.Embed):
        # ここは必要ならDB化できる
        for channel in guild.text_channels:
            if "log" in channel.name:
                try:
                    await channel.send(embed=embed)
                    return
                except:
                    pass


# =====================
# SETUP
# =====================
async def setup(bot):
    await bot.add_cog(Logger(bot))
