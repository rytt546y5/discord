import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "verify_config.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# =====================
# VIEW
# =====================
class VerifyView(discord.ui.View):
    def __init__(self, role_id: int):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(
        label="認証する",
        style=discord.ButtonStyle.green,
        custom_id="verify_btn"
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(self.role_id)

        if not role:
            return await interaction.response.send_message(
                "❌ ロールが見つかりません",
                ephemeral=True
            )

        try:
            await interaction.user.add_roles(role)
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ 権限がありません",
                ephemeral=True
            )

        await interaction.response.send_message(
            "✅ 認証完了",
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
    @app_commands.default_permissions(administrator=True)
    async def panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        role: discord.Role
    ):
        data = load_data()
        data[str(interaction.guild.id)] = role.id
        save_data(data)

        embed = discord.Embed(
            title="認証パネル",
            description="ボタンを押して認証してください",
            color=discord.Color.blurple()
        )

        await channel.send(embed=embed, view=VerifyView(role.id))

        await interaction.response.send_message(
            "✅ 設置完了",
            ephemeral=True
        )

    @app_commands.command(
        name="verify_reload",
        description="認証ボタン復元（再起動用）"
    )
    async def reload(self, interaction: discord.Interaction):
        data = load_data()
        role_id = data.get(str(interaction.guild.id))

        if not role_id:
            return await interaction.response.send_message(
                "❌ データなし",
                ephemeral=True
            )

        self.bot.add_view(VerifyView(role_id))

        await interaction.response.send_message(
            "✅ 復元完了",
            ephemeral=True
        )


# =====================
# SETUP
# =====================
async def setup(bot):
    await bot.add_cog(Verify(bot))
