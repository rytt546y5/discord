import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# =====================
# DATA
# =====================

DATA_FILE = "ticket_data.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# =====================
# VIEW（チケット作成）
# =====================

class TicketView(discord.ui.View):
    def __init__(self, staff_role_id: int):
        super().__init__(timeout=None)
        self.staff_role_id = staff_role_id

    @discord.ui.button(
        label="🎟 チケット作成",
        style=discord.ButtonStyle.green,
        custom_id="ticket_create_v2"
    )
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        user = interaction.user

        # 重複防止
        existing = discord.utils.get(
            guild.channels,
            name=f"ticket-{user.id}"
        )

        if existing:
            return await interaction.response.send_message(
                f"❌ 既にチケットがあります: {existing.mention}",
                ephemeral=True
            )

        # チャンネル作成
        channel = await guild.create_text_channel(
            name=f"ticket-{user.id}"
        )

        # 権限設定
        await channel.set_permissions(guild.default_role, view_channel=False)
        await channel.set_permissions(user, view_channel=True, send_messages=True)

        role = guild.get_role(self.staff_role_id)

        embed = discord.Embed(
            title="🎟 Ticket作成完了",
            description="サポートが来るまでお待ちください",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📌 通知",
            value=f"{role.mention if role else 'スタッフ'} に通知されます",
            inline=False
        )

        await channel.send(
            content=role.mention if role else None,
            embed=embed,
            view=TicketCloseView()
        )

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
        custom_id="ticket_close_v2"
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not (
            interaction.user.guild_permissions.administrator or
            interaction.user.guild_permissions.manage_channels
        ):
            return await interaction.response.send_message(
                "❌ 管理者のみ可能です",
                ephemeral=True
            )

        await interaction.response.send_message(
            "🔒 チケット削除中...",
            ephemeral=True
        )

        await interaction.channel.delete()


# =====================
# COG
# =====================

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # パネル設置
    # =====================

    @app_commands.command(
        name="ticket_panel",
        description="チケットパネル設置"
    )
    async def ticket_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        staff_role: discord.Role,
        title: str = "🎫 Ticket",
        description: str = "ボタンでチケットを作成できます",
        image: discord.Attachment = None
    ):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="🎟 作成方法",
            value="ボタンを押すだけ",
            inline=False
        )

        embed.add_field(
            name="📣 通知",
            value=f"{staff_role.mention} に通知されます",
            inline=False
        )

        if image:
            embed.set_image(url=image.url)

        msg = await channel.send(
            embed=embed,
            view=TicketView(staff_role.id)
        )

        # 保存（ここが重要）
        data = load_data()

        data[str(msg.id)] = {
            "guild_id": interaction.guild.id,
            "staff_role_id": staff_role.id
        }

        save_data(data)

        await interaction.response.send_message(
            "✅ ticketパネル設置完了",
            ephemeral=True
        )


# =====================
# SETUP（永続復元）
# =====================

async def setup(bot):

    data = load_data()
    loaded = set()

    for panel in data.values():

        role_id = panel.get("staff_role_id")

        if not role_id:
            continue

        if role_id in loaded:
            continue

        loaded.add(role_id)

        bot.add_view(
            TicketView(role_id)
        )

    await bot.add_cog(TicketCog(bot))
