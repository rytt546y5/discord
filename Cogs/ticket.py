import discord
from discord.ext import commands
from discord import app_commands

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 チケットを閉じる", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ チケットを閉じます...", ephemeral=True)
        await interaction.channel.delete()


class TicketView(discord.ui.View):
    def __init__(self, staff_role_id: int):
        super().__init__(timeout=None)
        self.staff_role_id = staff_role_id

    @discord.ui.button(label="🎫 チケット発行", style=discord.ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        member = interaction.user

        existing = discord.utils.get(
            guild.channels,
            name=f"ticket-{member.id}"
        )

        if existing:
            return await interaction.response.send_message(
                "❌ 既にチケットを作成しています。",
                ephemeral=True
            )

        staff_role = guild.get_role(self.staff_role_id)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
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
            name=f"ticket-{member.id}",
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 チケット作成",
            description=(
                f"{member.mention} さんのチケットです。\n\n"
                "内容をご記入ください。"
            ),
            color=discord.Color.green()
        )

        await channel.send(
            content=staff_role.mention if staff_role else None,
            embed=embed,
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"✅ {channel.mention} を作成しました。",
            ephemeral=True
        )


class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ticket",
        description="チケットパネルを作成します"
    )
    @app_commands.default_permissions(administrator=True)
    async def ticket(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        staff_role: discord.Role
    ):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )

        view = TicketView(staff_role.id)

        await interaction.channel.send(
            embed=embed,
            view=view
        )

        await interaction.response.send_message(
            "✅ チケットパネルを作成しました。",
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketView(0))
        self.bot.add_view(CloseTicketView())


async def setup(bot):
    await bot.add_cog(TicketCog(bot))
