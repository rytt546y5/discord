import discord
from discord.ext import commands
from discord import app_commands


# =====================
# VIEW（永続ボタン）
# =====================
class VerifyView(discord.ui.View):
    def __init__(self, role_id: int):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(
        label="認証する",
        style=discord.ButtonStyle.success,
        custom_id="verify_button"
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(self.role_id)

        if role is None:
            return await interaction.response.send_message(
                "❌ ロールが見つかりません",
                ephemeral=True
            )

        if role in interaction.user.roles:
            return await interaction.response.send_message(
                "⚠️ すでに認証済みです",
                ephemeral=True
            )

        await interaction.user.add_roles(role)

        await interaction.response.send_message(
            "✅ 認証完了しました",
            ephemeral=True
        )


# =====================
# COG
# =====================
class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="verify_panel",
        description="認証パネル設置"
    )
    async def verify_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        role: discord.Role,
        title: str = "認証パネル",
        description: str = "ボタンを押して認証してください",
        image: discord.Attachment = None
    ):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📌 認証",
            value=f"このボタンで {role.mention} を付与します",
            inline=False
        )

        if image:
            embed.set_image(url=image.url)

        await channel.send(
            embed=embed,
            view=VerifyView(role.id)
        )

        await interaction.response.send_message(
            "✅ verifyパネル設置完了",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Verify(bot))
