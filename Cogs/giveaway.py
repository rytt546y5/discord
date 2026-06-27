# giveaway_log.pyを削除する場合の giveaway.py
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random

DATA_FILE = "giveaway_data.json"
def load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

class GiveawayView(discord.ui.View):
    def __init__(self, message_id: int):
        super().__init__(timeout=None)
        self.message_id = message_id

    @discord.ui.button(label="🎉 参加する", style=discord.ButtonStyle.green, custom_id="giveaway_join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        gid = str(self.message_id)
        if gid not in data: data[gid] = {"users": []}
        if interaction.user.id in data[gid]["users"]:
            return await interaction.response.send_message("⚠ 参加済みです", ephemeral=True)
        data[gid]["users"].append(interaction.user.id)
        save_data(data)
        await interaction.response.send_message("✅ 参加しました！", ephemeral=True)

class Giveaway(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="giveaway_panel", description="抽選パネル設置")
    async def giveaway_panel(self, interaction: discord.Interaction, channel: discord.TextChannel, title: str, description: str, image: discord.Attachment = None):
        embed = discord.Embed(title=title, description=description, color=discord.Color.gold())
        if image: embed.set_image(url=image.url)
        
        msg = await channel.send(embed=embed) 
        view = GiveawayView(msg.id)
        await msg.edit(view=view)

        data = load_data()
        data[str(msg.id)] = {"guild_id": interaction.guild.id, "users": []}
        save_data(data)
        await interaction.response.send_message(f"✅ 設置完了", ephemeral=True)

    @app_commands.command(name="giveaway_pick", description="当選者選出")
    async def pick(self, interaction: discord.Interaction, message_id: str):
        data = load_data()
        users = data.get(message_id, {}).get("users", [])
        if not users: return await interaction.response.send_message("❌ 参加者なし", ephemeral=True)
        
        winner_id = random.choice(users)
        await interaction.response.send_message(f"🎉 当選者: <@{winner_id}>")

async def setup(bot):
    data = load_data()
    for msg_id in data.keys():
        if msg_id.isdigit(): bot.add_view(GiveawayView(int(msg_id)))
    await bot.add_cog(Giveaway(bot))
