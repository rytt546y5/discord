import discord
from discord.ext import commands
from discord import app_commands


# =====================
# VIEW（認証ボタン）
# =====================
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="✅ 認証する",
        style=discord.ButtonStyle.success,
        custom_id="verify_button"
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = discord.utils.get(
            interaction.guild.roles,
            name="verified"
        )

        if not role:
            return await interaction.response.send_message(
                "❌ verifiedロールがありません",
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
        description="認証パネルを設置"
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

        embed.add_field(
            name="📌 認証",
            value="ボタンを押すと認証されます",
            inline=False
        )

        if image:
            embed.set_image(url=image.url)

        await channel.send(
            embed=embed,
            view=VerifyView()
        )

        await interaction.response.send_message(
            "✅ verifyパネル設置完了",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Verify(bot))
