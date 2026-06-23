import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = “verify_config.json”

=====================

DATA

=====================

def load_data():
if not os.path.exists(DATA_FILE):
return {}

with open(DATA_FILE, "r", encoding="utf-8") as f:
    return json.load(f)

def save_data(data):
with open(DATA_FILE, “w”, encoding=“utf-8”) as f:
json.dump(
data,
f,
indent=2,
ensure_ascii=False
)

=====================

VIEW

=====================

class VerifyView(discord.ui.View):
def init(self):
super().init(timeout=None)

@discord.ui.button(
    label="認証する",
    style=discord.ButtonStyle.success,
    custom_id="verify_button"
)
async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
    data = load_data()
    config = data.get(str(interaction.channel.id))
    if not config:
        return await interaction.response.send_message(
            "❌ 認証設定が見つかりません",
            ephemeral=True
        )
    role_id = config["role_id"]
    role = interaction.guild.get_role(role_id)
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
    try:
        await interaction.user.add_roles(role)
        await interaction.response.send_message(
            "✅ 認証完了しました",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ ロール階層の問題で付与できません",
            ephemeral=True
        )

=====================

COG

=====================

class Verify(commands.Cog):
def init(self, bot):
self.bot = bot

@app_commands.command(
    name="verify_panel",
    description="認証パネルを設置します"
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
        name="📌 認証方法",
        value=f"ボタンを押すと {role.mention} が付与されます",
        inline=False
    )
    if image:
        embed.set_image(url=image.url)
    msg = await channel.send(
        embed=embed,
        view=VerifyView()
    )
    data = load_data()
    data[str(msg.channel.id)] = {
        "role_id": role.id
    }
    save_data(data)
    await interaction.response.send_message(
        "✅ verifyパネル設置完了",
        ephemeral=True
    )

=====================

SETUP

=====================

async def setup(bot):
await bot.add_cog(Verify(bot))
