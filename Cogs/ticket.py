import discord
from discord.ext import commands
from discord import app_commands


# =====================
# VIEW（チケット作成）
# =====================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎟 チケット作成",
        style=discord.ButtonStyle.green,
        custom_id="ticket_create"
    )
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):

        # 💥デバッグログ（これ超重要）
        print("🔥 TICKET BUTTON CLICKED")

        guild = interaction.guild
        user = interaction.user

        # 重複防止チェック
        existing = discord.utils.get(guild.channels, name=f"ticket-{user.id}")
        if existing:
            print("⚠ 既存チケットあり")
            return await interaction.response.send_message(
                f"❌ 既にチケットがあります: {existing.mention}",
                ephemeral=True
            )

        # チャンネル作成
        channel = await guild.create_text_channel(
            name=f"ticket-{user.id}"
        )

        print(f"📁 チケット作成: {channel.name}")

        # 権限設定
        await channel.set_permissions(guild.default_role, view_channel=False)
        await channel.set_permissions(user, view_channel=True, send_messages=True)

        embed = discord.Embed(
            title="🎟 Ticket作成完了",
            description="サポートが来るまでお待ちください",
            color=discord.Color.green()
        )

        await channel.send(embed=embed, view=TicketCloseView())

        await interaction.response.send_message(
            f"✅ チケット作成: {channel.mention}",
            ephemeral=True
        )


# =====================
# VIEW（クローズ）
# =====================
class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 チケットを閉じる",
        style=discord.ButtonStyle.red,
        custom_id="ticket_close"
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        print("🔒 CLOSE BUTTON CLICKED")

        user = interaction.user

        if not (
            user.guild_permissions.administrator or
            user.guild_permissions.manage_channels
        ):
            print("❌ 権限なし")
            return await interaction.response.send_message(
                "❌ この操作は管理者のみ可能です",
                ephemeral=True
            )

        await interaction.response.send_message(
            "🔒 チケットを削除します...",
            ephemeral=True
        )

        print(f"🗑 削除: {interaction.channel.name}")

        await interaction.channel.delete()


# =====================
# COG
# =====================
class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ticket_panel",
        description="チケットパネルを設置します"
    )
    @app_commands.describe(
        channel="設置チャンネル",
        title="タイトル",
        description="説明文",
        image="画像（任意）"
    )
    async def ticket_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        description: str,
        image: discord.Attachment = None
    ):

        print("📌 ticket_panel EXECUTED")

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="🎫 Ticketの使い方",
            value="ボタンを押すと専用チャンネルが作成されます",
            inline=False
        )

        if image:
            embed.set_image(url=image.url)

        await channel.send(
            embed=embed,
            view=TicketView()
        )

        await interaction.response.send_message(
            "✅ ticketパネル設置完了",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(TicketCog(bot))
