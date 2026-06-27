import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re

# =====================
# DATA
# =====================

DATA_FILE = "ticket_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =====================
# VIEW（チケット内の操作パネル）
# =====================

class TicketActionView(discord.ui.View):
    def __init__(self, staff_role_id: int):
        super().__init__(timeout=None)
        self.staff_role_id = staff_role_id

    @discord.ui.button(
        label="🤝 対応する",
        style=discord.ButtonStyle.primary,
        custom_id="ticket_claim_v2"
    )
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 権限チェック (スタッフロール保持者 or 管理者)
        role = interaction.guild.get_role(self.staff_role_id)
        is_staff = role in interaction.user.roles if role else False
        is_admin = interaction.user.guild_permissions.manage_channels

        if not (is_staff or is_admin):
            return await interaction.response.send_message("❌ この操作は担当スタッフのみ可能です。", ephemeral=True)

        # チャンネル名からユーザーIDを抽出 (ticket-123456789)
        user_id_match = re.search(r"ticket-(\d+)", interaction.channel.name)
        user_mention = f"<@{user_id_match.group(1)}>" if user_id_match else "お客様"

        # 対応開始のEmbed (プロフェッショナルな言い回し)
        embed = discord.Embed(
            title="📝 担当者決定のお知らせ",
            description=f"{interaction.user.mention} が本件の担当として入りました。\nご確認のほどよろしくお願いいたします。",
            color=discord.Color.blue()
        )
        embed.add_field(name="担当スタッフ", value=interaction.user.mention, inline=True)
        embed.add_field(name="対象ユーザー", value=user_mention, inline=True)
        embed.set_footer(text="只今より対応を開始いたします。")

        # 「対応する」ボタンだけを削除してメッセージを更新
        self.remove_item(button)
        await interaction.response.edit_message(view=self)
        
        # チャンネル内に通知
        await interaction.channel.send(content=f"{user_mention} {interaction.user.mention}", embed=embed)

    @discord.ui.button(
        label="🔒 チケットを閉じる",
        style=discord.ButtonStyle.red,
        custom_id="ticket_close_v2"
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not (interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_channels):
            return await interaction.response.send_message("❌ チケットを閉じる権限がありません（管理者・管理権限が必要）。", ephemeral=True)

        await interaction.response.send_message("🔒 チケットをクローズしています...", ephemeral=True)
        await interaction.channel.delete()

# =====================
# VIEW（チケット作成パネル）
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

        existing = discord.utils.get(guild.channels, name=f"ticket-{user.id}")
        if existing:
            return await interaction.response.send_message(f"❌ 既にチケットがあります: {existing.mention}", ephemeral=True)

        # チャンネル作成
        channel = await guild.create_text_channel(name=f"ticket-{user.id}")
        await channel.set_permissions(guild.default_role, view_channel=False)
        await channel.set_permissions(user, view_channel=True, send_messages=True)

        role = guild.get_role(self.staff_role_id)
        if role:
            await channel.set_permissions(role, view_channel=True, send_messages=True)

        embed = discord.Embed(
            title="🎟 Ticket作成完了",
            description=f"{user.mention} 様、お問い合わせありがとうございます。\nスタッフが対応いたしますので、内容を記載してお待ちください。",
            color=discord.Color.green()
        )
        embed.add_field(name="📌 担当スタッフ", value=f"{role.mention if role else '確認中'}", inline=False)

        # チケット内に「対応する」「閉じる」ボタンを設置
        await channel.send(
            content=f"{role.mention if role else ''} {user.mention}",
            embed=embed,
            view=TicketActionView(self.staff_role_id)
        )

        await interaction.response.send_message(f"✅ チケットを作成しました: {channel.mention}", ephemeral=True)

# =====================
# COG
# =====================

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket_panel", description="チケットパネルを設置します")
    @app_commands.describe(
        channel="設置するチャンネル",
        staff_role="対応にあたるスタッフロール",
        title="パネルのタイトル",
        description="パネルの説明文"
    )
    async def ticket_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        staff_role: discord.Role,
        title: str = "🎫 お問い合わせ",
        description: str = "ご用件の方は下のボタンを押してチケットを作成してください。",
        image: discord.Attachment = None
    ):
        embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
        embed.add_field(name="🎟 作成方法", value="「チケット作成」ボタンを押してください。", inline=False)
        embed.add_field(name="📣 通知先", value=staff_role.mention, inline=False)
        if image:
            embed.set_image(url=image.url)

        msg = await channel.send(embed=embed, view=TicketView(staff_role.id))

        data = load_data()
        data[str(msg.id)] = {
            "guild_id": interaction.guild.id,
            "staff_role_id": staff_role.id
        }
        save_data(data)

        await interaction.response.send_message("✅ チケットパネルを設置しました。", ephemeral=True)

# =====================
# SETUP
# =====================

async def setup(bot):
    data = load_data()
    # 登録済みのすべてのViewを復元
    for panel in data.values():
        role_id = panel.get("staff_role_id")
        if role_id:
            bot.add_view(TicketView(role_id))
            bot.add_view(TicketActionView(role_id)) # チケット内のViewも復元対象に追加

    await bot.add_cog(TicketCog(bot))
