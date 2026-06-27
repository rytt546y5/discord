import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re
import io
import datetime

# =====================
# DATA
# =====================
DATA_FILE = "ticket_data.json"

def load_json(file):
    if not os.path.exists(file): return {}
    with open(file, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =====================
# HTML Transcript 生成
# =====================
def generate_html_transcript(channel_name, owner_name, claimed_by, closed_by, messages, reason="なし"):
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background-color: #36393f; color: #dcddde; font-family: sans-serif; padding: 20px; }}
            .header {{ border-bottom: 1px solid #4f545c; padding-bottom: 20px; margin-bottom: 20px; }}
            .message {{ display: flex; margin-bottom: 15px; }}
            .avatar {{ width: 40px; height: 40px; border-radius: 50%; margin-right: 15px; }}
            .author {{ font-weight: bold; color: #fff; margin-right: 5px; }}
            .time {{ color: #72767d; font-size: 0.75em; }}
            .text {{ margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1># {channel_name} 履歴</h1>
            <div>作成者: {owner_name} | 担当者: {claimed_by} | 終了者: {closed_by} | 理由: {reason}</div>
        </div>
    """
    for msg in messages:
        avatar_url = msg.author.display_avatar.url
        time_str = msg.created_at.strftime("%Y/%m/%d %H:%M")
        clean_content = msg.clean_content.replace("\n", "<br>")
        html += f"""
        <div class="message">
            <img src="{avatar_url}" class="avatar">
            <div>
                <div><span class="author">{msg.author.display_name}</span><span class="time">{time_str}</span></div>
                <div class="text">{clean_content}</div>
            </div>
        </div>
        """
    html += "</body></html>"
    return html

# =====================
# 権限チェック関数
# =====================
def can_manage_ticket(interaction, staff_role_id):
    role = interaction.guild.get_role(staff_role_id)
    is_staff = role in interaction.user.roles if role else False
    is_admin = interaction.user.guild_permissions.manage_channels or interaction.user.guild_permissions.administrator
    return is_staff or is_admin

# =====================
# MODAL（理由付きクローズ）
# =====================
class CloseReasonModal(discord.ui.Modal, title="チケットを閉じる"):
    reason = discord.ui.TextInput(label="理由を入力してください", style=discord.TextStyle.short, placeholder="対応完了、解決済みなど", required=False)

    def __init__(self, action_view):
        super().__init__()
        self.action_view = action_view

    async def on_submit(self, interaction: discord.Interaction):
        # モーダル送信時にもう一度権限チェック
        if not can_manage_ticket(interaction, self.action_view.staff_role_id):
            return await interaction.response.send_message("❌ 権限がありません。", ephemeral=True)
        await self.action_view.execute_close(interaction, reason=self.reason.value)

# =====================
# VIEW（チケット内の操作パネル）
# =====================
class TicketActionView(discord.ui.View):
    def __init__(self, staff_role_id: int):
        super().__init__(timeout=None)
        self.staff_role_id = staff_role_id
        self.claimed_by = None

    @discord.ui.button(label="このチケットを担当する", style=discord.ButtonStyle.success, custom_id="ticket_claim_v2", emoji="🤝")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not can_manage_ticket(interaction, self.staff_role_id):
            return await interaction.response.send_message("❌ スタッフのみ対応可能です。", ephemeral=True)

        self.claimed_by = interaction.user
        embed = discord.Embed(title="🤝 担当者が決定しました", description=f"{interaction.user.mention} がこのチケットを担当します。", color=discord.Color.blue())
        self.remove_item(button)
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=embed)

    @discord.ui.button(label="閉じる", style=discord.ButtonStyle.danger, custom_id="ticket_close_v2", emoji="🔒")
    async def close_confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not can_manage_ticket(interaction, self.staff_role_id):
            return await interaction.response.send_message("❌ 権限がありません。", ephemeral=True)

        # 確認用View
        view = discord.ui.View()
        btn = discord.ui.Button(label="チケットを閉じる(最終確認)", style=discord.ButtonStyle.danger, emoji="✅")
        async def confirm_callback(it: discord.Interaction):
            if not can_manage_ticket(it, self.staff_role_id):
                return await it.response.send_message("❌ 権限がありません。", ephemeral=True)
            await self.execute_close(it)
        btn.callback = confirm_callback
        view.add_item(btn)
        
        embed = discord.Embed(title="確認", description="このチケットを閉じてもよろしいですか？\n(履歴は自動で作成されます)", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="理由付きで閉じる", style=discord.ButtonStyle.secondary, custom_id="ticket_close_reason_v2", emoji="📝")
    async def close_with_reason(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not can_manage_ticket(interaction, self.staff_role_id):
            return await interaction.response.send_message("❌ 権限がありません。", ephemeral=True)
        await interaction.response.send_modal(CloseReasonModal(self))

    async def execute_close(self, interaction: discord.Interaction, reason="特になし"):
        await interaction.response.send_message("⌛ ログ(HTML形式)を生成して、DMへ送信中...", ephemeral=True)

        user_id_match = re.search(r"ticket-(\d+)", interaction.channel.name)
        owner_id = user_id_match.group(1) if user_id_match else None
        owner = interaction.guild.get_member(int(owner_id)) if owner_id else None

        # 履歴取得
        messages = [msg async for msg in interaction.channel.history(limit=None, oldest_first=True)]
        
        # HTML作成
        html_str = generate_html_transcript(
            interaction.channel.name,
            str(owner) if owner else "不明",
            str(self.claimed_by) if self.claimed_by else "未担当",
            str(interaction.user),
            messages,
            reason
        )
        
        file_bytes = html_str.encode("utf-8")
        filename = f"log-{interaction.channel.name}.html"

        log_embed = discord.Embed(title="📑 チケット終了ログ", description=f"チケット `{interaction.channel.name}` が終了しました。", color=discord.Color.dark_gray())
        log_embed.add_field(name="終了理由", value=reason)

        # 送信 (本人とスタッフ)
        for target in [interaction.user, owner]:
            if target:
                try:
                    await target.send(embed=log_embed, file=discord.File(io.BytesIO(file_bytes), filename=filename))
                except: pass

        await interaction.channel.delete()

# =====================
# VIEW（チケット作成パネル）
# =====================
class TicketView(discord.ui.View):
    def __init__(self, staff_role_id: int):
        super().__init__(timeout=None)
        self.staff_role_id = staff_role_id

    @discord.ui.button(label="🎟 チケット作成", style=discord.ButtonStyle.green, custom_id="ticket_create_v2")
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        existing = discord.utils.get(guild.channels, name=f"ticket-{user.id}")
        if existing: return await interaction.response.send_message(f"❌ 既にチケットがあります: {existing.mention}", ephemeral=True)

        channel = await guild.create_text_channel(name=f"ticket-{user.id}")
        await channel.set_permissions(guild.default_role, view_channel=False)
        await channel.set_permissions(user, view_channel=True, send_messages=True)

        role = guild.get_role(self.staff_role_id)
        if role: await channel.set_permissions(role, view_channel=True, send_messages=True)

        embed = discord.Embed(title="🎟 お問い合わせ受領", description=f"{user.mention} 様、お問い合わせありがとうございます。\nスタッフが対応するまで、内容を詳しくお書きください。", color=discord.Color.green())
        await channel.send(content=f"{role.mention if role else ''} {user.mention}", embed=embed, view=TicketActionView(self.staff_role_id))
        await interaction.response.send_message(f"✅ チケットを作成しました: {channel.mention}", ephemeral=True)

# =====================
# COG / SETUP
# =====================
class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket_panel", description="チケット作成パネルを設置します")
    @app_commands.describe(title="パネルのタイトル", description="パネルの説明文", staff_role="対応スタッフロール")
    async def ticket_panel(self, interaction: discord.Interaction, channel: discord.TextChannel, staff_role: discord.Role, title: str = "🎫 サポートチケット", description: str = "下のボタンを押してチケットを作成してください。"):
        embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
        await channel.send(embed=embed, view=TicketView(staff_role.id))
        
        data = load_json(DATA_FILE)
        data[str(interaction.guild.id)] = {"staff_role_id": staff_role.id} # シンプルにギルド単位で保存
        save_json(DATA_FILE, data)
        await interaction.response.send_message("✅ パネルを設置しました。", ephemeral=True)

async def setup(bot):
    data = load_json(DATA_FILE)
    # 全ギルドのViewを登録
    for gid, info in data.items():
        role_id = info.get("staff_role_id")
        if role_id:
            bot.add_view(TicketView(role_id))
            bot.add_view(TicketActionView(role_id))
    await bot.add_cog(TicketCog(bot))
