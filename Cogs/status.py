import discord
from discord.ext import commands
from discord import app_commands
import json
import os

CONFIG_FILE = “ticket_config.json”

def load_data():
if not os.path.exists(CONFIG_FILE):
return {}

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    return json.load(f)

def save_data(data):
with open(CONFIG_FILE, “w”, encoding=“utf-8”) as f:
json.dump(data, f, indent=4)

class CloseTicketView(discord.ui.View):
def init(self, staff_role_id: int):
super().init(timeout=None)
self.staff_role_id = staff_role_id

@discord.ui.button(
    label="🔒 チケットを閉じる",
    style=discord.ButtonStyle.red,
    custom_id="close_ticket"
)
async def close_ticket(
    self,
    interaction: discord.Interaction,
    button: discord.ui.Button
):
    staff_role = interaction.guild.get_role(
        self.staff_role_id
    )
    if (
        staff_role
        and staff_role not in interaction.user.roles
    ):
        return await interaction.response.send_message(
            "❌ スタッフのみ閉じられます",
            ephemeral=True
        )
    await interaction.response.send_message(
        "🗑️ チケットを削除します...",
        ephemeral=True
    )
    await interaction.channel.delete()

class TicketView(discord.ui.View):
def init(self, staff_role_id: int):
super().init(timeout=None)
self.staff_role_id = staff_role_id

@discord.ui.button(
    label="🎫 チケット発行",
    style=discord.ButtonStyle.green,
    custom_id="create_ticket"
)
async def create_ticket(
    self,
    interaction: discord.Interaction,
    button: discord.ui.Button
):
    guild = interaction.guild
    member = interaction.user
    existing = discord.utils.get(
        guild.channels,
        name=f"ticket-{member.id}"
    )
    if existing:
        return await interaction.response.send_message(
            "❌ 既にチケットがあります",
            ephemeral=True
        )
    staff_role = guild.get_role(
        self.staff_role_id
    )
    overwrites = {
        guild.default_role:
            discord.PermissionOverwrite(
                view_channel=False
            ),
        member:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
        guild.me:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                read_message_history=True
            )
    }
    if staff_role:
        overwrites[staff_role] = (
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
        )
    channel = await guild.create_text_channel(
        name=f"ticket-{member.id}",
        overwrites=overwrites
    )
    embed = discord.Embed(
        title="🎫 チケット作成",
        description=f"{member.mention} さんのチケットです",
        color=discord.Color.green()
    )
    await channel.send(
        content=staff_role.mention if staff_role else None,
        embed=embed,
        view=CloseTicketView(
            self.staff_role_id
        )
    )
    await interaction.response.send_message(
        f"✅ {channel.mention} を作成しました",
        ephemeral=True
    )

class TicketCog(commands.Cog):
def init(self, bot):
self.bot = bot

@app_commands.command(
    name="ticket",
    description="チケットパネルを設置します"
)
@app_commands.default_permissions(
    administrator=True
)
async def ticket(
    self,
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    title: str,
    description: str,
    staff_role: discord.Role,
    image_url: str = None
):
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blurple()
    )
    if image_url:
        embed.set_image(
            url=image_url
        )
    view = TicketView(
        staff_role.id
    )
    await channel.send(
        embed=embed,
        view=view
    )
    data = load_data()
    data[str(interaction.guild.id)] = {
        "staff_role_id": staff_role.id
    }
    save_data(data)
    await interaction.response.send_message(
        "✅ チケットパネル設置完了",
        ephemeral=True
    )
@commands.Cog.listener()
async def on_ready(self):
    data = load_data()
    for guild_id, value in data.items():
        try:
            self.bot.add_view(
                TicketView(
                    value["staff_role_id"]
                )
            )
            self.bot.add_view(
                CloseTicketView(
                    value["staff_role_id"]
                )
            )
        except Exception as e:
            print(
                f"Ticket Restore Error: {e}"
            )

async def setup(bot):
await bot.add_cog(
TicketCog(bot)
)
