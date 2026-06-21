import discord
from discord.ext import commands
from discord import app_commands


class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # TICKETパネル設置
    # =====================
    @app_commands.command(
        name="ticket_panel",
        description="チケットパネルを設置します"
    )
    @app_commands.describe(
        channel="設置するチャンネル",
        title="パネルタイトル",
        description="説明文",
        image="画像（任意・添付ファイル）"
    )
    async def ticket_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        description: str,
        image: discord.Attachment = None
    ):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.green()
        )

        if image:
            embed.set_image(url=image.url)

        embed.add_field(
            name="🎟 Ticketについて",
            value="ボタンを押すとサポートチケットが作成されます",
            inline=False
        )

        await channel.send(embed=embed, view=TicketView())

        await interaction.response.send_message(
            "✅ ticketパネル設置完了",
            ephemeral=True
        )


# =====================
# TICKET VIEW
# =====================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎟 チケット作成",
        style=discord.ButtonStyle.green,
        custom_id="ticket_create"
    )
    async def create(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = interaction.guild

        # チャンネル作成
        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}"
        )

        await channel.set_permissions(guild.default_role, read_messages=False)
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)

        await interaction.response.send_message(
            f"✅ チケット作成: {channel.mention}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(TicketCog(bot))
