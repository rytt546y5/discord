import discord
from discord.ext import commands
from discord import app_commands


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

        embed = discord.Embed(
            title="📩 Botからのメッセージ",
            description=message,
            color=discord.Color.green()
        )

        embed.set_footer(text=f"From: {interaction.user}")

        try:
            await user.send(embed=embed)

            await interaction.response.send_message(
                f"✅ {user.name} にDM送信しました",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ DMを送信できません（DM拒否の可能性）",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(DM(bot))
