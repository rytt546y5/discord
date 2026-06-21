import discord
from discord.ext import commands
from discord import app_commands


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # VERIFY PANEL設置
    # =====================
    @app_commands.command(
        name="verify_panel",
        description="認証パネルを設置します"
    )
    @app_commands.describe(
        channel="設置するチャンネル",
        title="パネルのタイトル",
        description="パネルの説明",
        image="画像（任意・添付ファイル）"
    )
    async def verify_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        description: str,
        image: discord.Attachment = None
    ):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )

        if image:
            embed.set_image(url=image.url)

        embed.add_field(
            name="📌 認証について",
            value="ボタンを押すと認証ロールが付与されます",
            inline=False
        )

        await channel.send(embed=embed)
        await interaction.response.send_message(
            "✅ verifyパネル設置完了",
            ephemeral=True
        )

    # =====================
    # VERIFY 実行コマンド
    # =====================
    @app_commands.command(
        name="verify",
        description="認証を実行します"
    )
    async def verify(self, interaction: discord.Interaction):

        role = discord.utils.get(
            interaction.guild.roles,
            name="verified"
        )

        if not role:
            return await interaction.response.send_message(
                "❌ verifiedロールが見つかりません",
                ephemeral=True
            )

        await interaction.user.add_roles(role)

        await interaction.response.send_message(
            "✅ 認証完了しました",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Verify(bot))
