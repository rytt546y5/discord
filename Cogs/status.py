import discord
from discord.ext import commands
from discord import app_commands
import json
import os
STATUS_FILE = "status.json"
def load_status():
    if not os.path.exists(STATUS_FILE):
        return {}
    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
def save_status(data):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
class StatusView(discord.ui.View):
    def __init__(self, bot, message_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.message_id = message_id
    async def update_panel(self, interaction: discord.Interaction, status: str):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ 管理者のみ使用できます",
                ephemeral=True
            )
        data = load_status()
        guild_id = str(interaction.guild.id)
        data[guild_id] = {
            "status": status,
            "user_id": interaction.user.id,
            "message_id": self.message_id
        }
        save_status(data)
        channel = interaction.channel
        message = await channel.fetch_message(self.message_id)
        color = {
            "green": discord.Color.green(),
            "yellow": discord.Color.gold(),
            "red": discord.Color.red()
        }[status]
        text = {
            "green": "🟢 対応中",
            "yellow": "🟡 離席中",
            "red": "🔴 対応不可"
        }[status]
        embed = discord.Embed(
            title="対応ステータス",
            description=f"{text}\n\n更新者: <@{interaction.user.id}>",
            color=color
        )
        await message.edit(embed=embed, view=self)
        await interaction.response.send_message("更新しました", ephemeral=True)
    @discord.ui.button(label="🟢 対応中", style=discord.ButtonStyle.green, custom_id="status_green")
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_panel(interaction, "green")
    @discord.ui.button(label="🟡 離席中", style=discord.ButtonStyle.secondary, custom_id="status_yellow")
    async def yellow(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_panel(interaction, "yellow")
    @discord.ui.button(label="🔴 対応不可", style=discord.ButtonStyle.red, custom_id="status_red")
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_panel(interaction, "red")
class StatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @app_commands.command(name="対応パネル設置", description="対応ステータスパネルを設置します")
    @app_commands.default_permissions(administrator=True)
    async def panel(
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
        msg = await channel.send(embed=embed)
        view = StatusView(self.bot, msg.id)
        await msg.edit(view=view)
        data = load_status()
        data[str(interaction.guild.id)] = {
            "status": "green",
            "user_id": interaction.user.id,
            "message_id": msg.id
        }
        save_status(data)
        await interaction.response.send_message("設置完了", ephemeral=True)
    @commands.Cog.listener()
    async def on_ready(self):
        data = load_status()
        for guild_id, v in data.items():
            self.bot.add_view(StatusView(self.bot, v["message_id"]))
async def setup(bot):
    await bot.add_cog(StatusCog(bot))
