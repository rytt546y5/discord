import discord
from discord.ext import commands
from discord import app_commands


# =====================
# VIEW
# =====================
class VerifyView(discord.ui.View):
    def __init__(self, role: discord.Role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(
        label="認証する",
        style=discord.ButtonStyle.green,
        custom_id="verify_btn"
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        # ❌ 既にロール持ってる場合
        if self.role in interaction.user.roles:
            return await interaction.response.send_message(
                "すでに認証済みです",
                ephemeral=True
            )

        # ✔ ロール付与
        try:
            await interaction.user.add_roles(self.role)
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ 権限がありません（ロール付与できない）",
                ephemeral=True
            )

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

    # =====================
    # パネル設置コマンド
    # =====================
    @app_commands.command(
        name="verify_panel",
        description="認証パネルを設置します"
    )
    @app_commands.default_permissions(administrator=True)
    async def panel(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        channel: discord.TextChannel,
        role: discord.Role
    ):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.green()
        )

        await channel.send(
            embed=embed,
            view=VerifyView(role)
        )

        await interaction.response.send_message(
            "認証パネル設置完了",
            ephemeral=True
        )

    # =====================
    # 再起動対策（重要）
    # =====================
    @commands.Cog.listener()
    async def on_ready(self):
        # custom_idベースなので復元OK
        self.bot.add_view(VerifyView(role=discord.Object(id=0)))


# =====================
# SETUP
# =====================
async def setup(bot):
    await bot.add_cog(Verify(bot))
