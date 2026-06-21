import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "ticket_config.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# =====================
# CLOSE BUTTON
# =====================
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 チケットを閉じる",
        style=discord.ButtonStyle.red,
        custom_id="close_ticket"
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🗑 チケットを閉じています...",
            ephemeral=True
        )

        try:
            await interaction.channel.delete()
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ 削除権限がありません",
                ephemeral=True
            )


# =====================
# CREATE BUTTON
# =====================
class TicketView(discord.ui.View):
    def __init__(self, staff_role_id: int):
        super().__init__(timeout=None)
        self.staff_role_id = staff_role_id

    @discord.ui.button(
        label="🎫 チケット作成",
        style=discord.ButtonStyle.green,
        custom_id="create_ticket"
    )
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        existing = discord.utils.get(
            guild.channels,
            name=f"ticket-{user.id}"
        )

        if existing:
            return await interaction.response.send_message(
                "❌ すでにチケットがあります",
                ephemeral=True
            )

        staff_role = guild.get_role(self.staff_role_id)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                read_message_history=True
            )
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )

        channel = await guild.create_text_channel(
            name=f"ticket-{user.id}",
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 Ticket",
            description=f"{user.mention} のチケットです",
            color=discord.Color.green()
        )

        await channel.send(
            content=staff_role.mention if staff_role else None,
            embed=embed,
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"✅ 作成しました → {channel.mention}",
            ephemeral=True
        )


# =====================
# COG
# =====================
class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ticket",
        description="チケットパネル設置"
    )
    @app_commands.default_permissions(administrator=True)
    async def ticket(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        staff_role: discord.Role,
        title: str = "Ticket",
        description: str = "ボタンでチケットを作成できます",
        image_url: str = None
    ):
        data = load_data()
        data[str(interaction.guild.id)] = staff_role.id
        save_data(data)

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )

        # 💥画像対応
        if image_url:
            embed.set_image(url=image_url)

        await channel.send(
            embed=embed,
            view=TicketView(staff_role.id)
        )

        await interaction.response.send_message(
            "✅ チケットパネル設置完了",
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(CloseTicketView())


# =====================
# SETUP
# =====================
async def setup(bot):
    await bot.add_cog(TicketCog(bot))
