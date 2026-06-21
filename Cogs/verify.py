import discord
from discord.ext import commands
from discord import app_commands

class VerifyView(discord.ui.View):
def init(self, role_id: int):
super().init(timeout=None)
self.role_id = role_id

@discord.ui.button(
    label="✅ 認証する",
    style=discord.ButtonStyle.green,
    custom_id="verify_button"
)
async def verify(
    self,
    interaction: discord.Interaction,
    button: discord.ui.Button
):
    role = interaction.guild.get_role(
        self.role_id
    )
    if role is None:
        return await interaction.response.send_message(
            "❌ 認証ロールが見つかりません",
            ephemeral=True
        )
    if role in interaction.user.roles:
        return await interaction.response.send_message(
            "✅ 既に認証済みです",
            ephemeral=True
        )
    try:
        await interaction.user.add_roles(role)
    except discord.Forbidden:
        return await interaction.response.send_message(
            "❌ Botにロール付与権限がありません",
            ephemeral=True
        )
    await interaction.response.send_message(
        f"✅ {role.mention} を付与しました",
        ephemeral=True
    )

class Verify(commands.Cog):
def init(self, bot):
self.bot = bot

@app_commands.command(
    name="verify_panel",
    description="認証パネルを設置します"
)
@app_commands.default_permissions(
    administrator=True
)
async def verify_panel(
    self,
    interaction: discord.Interaction,
    title: str,
    description: str,
    channel: discord.TextChannel,
    role: discord.Role,
    image_url: str = None
):
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.green()
    )
    if image_url:
        embed.set_image(
            url=image_url
        )
    await channel.send(
        embed=embed,
        view=VerifyView(role.id)
    )
    await interaction.response.send_message(
        "✅ 認証パネルを設置しました",
        ephemeral=True
    )
@commands.Cog.listener()
async def on_ready(self):
    # 再起動後もボタンを生かす
    # role_idは押した時に取得するため仮値
    self.bot.add_view(
        VerifyView(0)
    )

async def setup(bot):
await bot.add_cog(
Verify(bot)
)
