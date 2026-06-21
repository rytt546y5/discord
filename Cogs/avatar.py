import discord
from discord.ext import commands
from discord import app_commands


class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="avatar",
        description="ユーザーのアバターを表示"
    )
    @app_commands.describe(
        user="対象ユーザー（未指定なら自分）"
    )
    async def avatar(
        self,
        interaction: discord.Interaction,
        user: discord.User = None
    ):

        user = user or interaction.user

        embed = discord.Embed(
            title=f"🖼 {user.name} のアバター",
            color=discord.Color.blurple()
        )

        embed.set_image(url=user.display_avatar.url)

        embed.set_footer(text="クリックで原寸表示可能")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Avatar(bot))
