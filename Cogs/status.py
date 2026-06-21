import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

class StatusView(discord.ui.View):
def init(self):
super().init(timeout=None)

async def update_status(
    self,
    interaction: discord.Interaction,
    status_text: str,
    color: discord.Color
):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(
            "❌ 管理者のみ使用できます",
            ephemeral=True
        )
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    embed = discord.Embed(
        title="対応ステータス",
        description=status_text,
        color=color
    )
    embed.add_field(
        name="更新者",
        value=interaction.user.mention,
        inline=False
    )
    embed.add_field(
        name="更新時刻",
        value=now,
        inline=False
    )
    await interaction.message.edit(
        embed=embed,
        view=self
    )
    await interaction.response.send_message(
        "✅ 更新しました",
        ephemeral=True
    )
@discord.ui.button(
    label="🟢 対応中",
    style=discord.ButtonStyle.green,
    custom_id="status_green"
)
async def green(
    self,
    interaction: discord.Interaction,
    button: discord.ui.Button
):
    await self.update_status(
        interaction,
        "🟢 対応中",
        discord.Color.green()
    )
@discord.ui.button(
    label="🟡 離席中",
    style=discord.ButtonStyle.secondary,
    custom_id="status_yellow"
)
async def yellow(
    self,
    interaction: discord.Interaction,
    button: discord.ui.Button
):
    await self.update_status(
        interaction,
        "🟡 離席中",
        discord.Color.gold()
    )
@discord.ui.button(
    label="🔴 対応不可",
    style=discord.ButtonStyle.red,
    custom_id="status_red"
)
async def red(
    self,
    interaction: discord.Interaction,
    button: discord.ui.Button
):
    await self.update_status(
        interaction,
        "🔴 対応不可",
        discord.Color.red()
    )

class StatusCog(commands.Cog):
def init(self, bot):
self.bot = bot

@app_commands.command(
    name="status_panel",
    description="対応ステータスパネルを設置します"
)
@app_commands.default_permissions(administrator=True)
async def status_panel(
    self,
    interaction: discord.Interaction,
    title: str,
    description: str,
    channel: discord.TextChannel
):
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blurple()
    )
    await channel.send(
        embed=embed,
        view=StatusView()
    )
    await interaction.response.send_message(
        "✅ ステータスパネルを設置しました",
        ephemeral=True
    )
@commands.Cog.listener()
async def on_ready(self):
    self.bot.add_view(StatusView())

async def setup(bot):
await bot.add_cog(StatusCog(bot))
