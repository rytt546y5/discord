import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional


class DM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="dm",
        description="指定ユーザーにDMを送信"
    )
    @app_commands.describe(
        user="送信対象ユーザー",
        message="送るメッセージ"
    )
    async def dm(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        message: str
    ):

        # 🔥 管理者制限（重要）
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ 管理者のみ使用できます",
                ephemeral=True
            )

        embed = discord.Embed(
            title="📩 Botからのメッセージ",
            description=message,
            color=discord.Color.green()
        )

        embed.set_footer(text=f"From: {interaction.user.name}")

        try:
            await user.send(embed=embed)

            await interaction.response.send_message(
                f"✅ {user.name} にDM送信しました",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ DM送信できません（相手がDM拒否中）",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(DM(bot))
