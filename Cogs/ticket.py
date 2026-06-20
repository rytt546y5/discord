import discord
from discord.ext import commands
from discord import app_commands


# ─────────────
# チケット削除ボタン（永続OK）
# ─────────────
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

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
        await interaction.response.send_message(
            "🗑️ チケットを閉じています...",
            ephemeral=True
        )
        await interaction.channel.delete()


# ─────────────
# チケット作成ボタン（パネル用）
# ─────────────
class TicketView(discord.ui.View):
    def __init__(self, staff_role_id: int):
        super().__init__(timeout=None)
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

        # 既存チェック
        existing = discord.utils.get(
            guild.channels,
            name=f"ticket-{member.id}"
        )

        if existing:
            return await interaction.response.send_message(
                "❌ 既にチケットがあります",
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
            description=f"{member.mention} さんのチケットです",
            color=discord.Color.green()
        )

        await channel.send(
            content=staff_role.mention if staff_role else None,
            embed=embed,
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"✅ {channel.mention} を作成しました",
            ephemeral=True
        )


# ─────────────
# Cog本体
# ─────────────
class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ticket",
        description="チケットパネルを設置します"
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

        await interaction.channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            "✅ チケットパネル設置完了",
            ephemeral=True
        )

    # ─────────────
    # 起動時（重要）
    # ─────────────
    @commands.Cog.listener()
    async def on_ready(self):
        # ★重要：Closeだけ復元（TicketViewは復元しない）
        self.bot.add_view(CloseTicketView())


async def setup(bot):
    await bot.add_cog(TicketCog(bot))
