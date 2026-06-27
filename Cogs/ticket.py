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
# HTML Transcript 生成関数
# =====================
def generate_html_transcript(channel_name, owner_name, claimed_by, closed_by, messages, reason="なし"):
    # シンプルなDiscord風デザインのHTML
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background-color: #36393f; color: #dcddde; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; padding: 20px; }}
            .header {{ border-bottom: 1px solid #4f545c; padding-bottom: 20px; margin-bottom: 20px; }}
            .ticket-info {{ color: #b9bbbe; font-size: 0.9em; }}
            .message {{ display: flex; margin-bottom: 15px; }}
            .avatar {{ width: 40px; height: 40px; border-radius: 50%; margin-right: 15px; }}
            .content {{ display: flex; flex-direction: column; }}
            .author {{ font-weight: bold; color: #fff; margin-right: 5px; }}
            .time {{ color: #72767d; font-size: 0.75em; }}
            .text {{ margin-top: 5px; line-height: 1.3; }}
            .reason-box {{ background: #2f3136; border-left: 4px solid #f04747; padding: 10px; margin: 10px 0; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1># {channel_name} - Transcript</h1>
            <div class="ticket-info">
                作成者: {owner_name} | 担当者: {claimed_by} | 終了者: {closed_by}<br>
                終了理由: {reason}
            </div>
        </div>
    """
    for msg in messages:
        # メッセージ一行ずつ追加
        avatar_url = msg.author.display_avatar.url
        time_str = msg.created_at.strftime("%Y/%m/%d %H:%M")
        clean_content = msg.clean_content.replace("\n", "<br>")
        html += f"""
        <div class="message">
            <img src="{avatar_url}" class="avatar">
            <div class="content">
                <div><span class="author">{msg.author.display_name}</span><span class="time">{time_str}</span></div>
                <div class="text">{clean_content}</div>
            </div>
        </div>
        """
    html += "</body></html>"
    return html

# =====================
# MODAL（理由付きクローズ用）
# =====================
class CloseReasonModal(discord.ui.Modal, title="チケットを閉じる"):
    reason = discord.ui.TextInput(label="理由を入力してください", style=discord.TextStyle.short, placeholder="例: 対応完了、質問解決など", required=False)

    def __init__(self, action_view):
        super().__init__()
        self.action_view = action_view

    async def on_submit(self, interaction: discord.Interaction):
        await self.action_view.execute_close(interaction, reason=self.reason.value)

# =====================
# VIEW（チケット内の操作パネル）
# =====================
class TicketActionView(discord.ui.View):
    def __init__(self, staff_role_id: int):
        super().__init__(timeout=None)
        self.staff_role_id = staff_role_id
        self.claimed_by = None

    @discord.ui.button(label="🤝 Claim", style=discord.ButtonStyle.success, custom_id="ticket_claim_v2", emoji="🙋‍♂️")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(self.staff_role_id)
        if not (role in interaction.user.roles or interaction.user.guild_permissions.manage_channels):
            return await interaction.response.send_message("❌ スタッフのみ対応可能です。", ephemeral=True)

        self.claimed_by = interaction.user
        embed = discord.Embed(title="🤝 担当者が決まりました", description=f"{interaction.user.mention} が対応を開始します。", color=discord.Color.blue())
        self.remove_item(button)
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=embed)

    @discord.ui.button(label="🔒 Close", style=discord.ButtonStyle.danger, custom_id="ticket_close_v2", emoji="🔒")
    async def close_confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 削除確認用ボタンを出す
        view = discord.ui.View()
        btn = discord.ui.Button(label="Close 確認", style=discord.ButtonStyle.danger, emoji="✅")
        async def confirm_callback(it: discord.Interaction):
            await self.execute_close(it)
        btn.callback = confirm_callback
        view.add_item(btn)
        
        embed = discord.Embed(title="Close Confirmation", description="本当にこのチケットを閉じますか？", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🔒 Close With Reason", style=discord.ButtonStyle.secondary, custom_id="ticket_close_reason_v2")
    async def close_with_reason(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CloseReasonModal(self))

    # 実際の削除・ログ送信処理
    async def execute_close(self, interaction: discord.Interaction, reason="なし"):
        await interaction.response.send_message("⌛ ログ(HTML)を生成中...", ephemeral=True)

        user_id_match = re.search(r"ticket-(\d+)", interaction.channel.name)
        owner_id = user_id_match.group(1) if user_id_match else None
        owner = interaction.guild.get_member(int(owner_id)) if owner_id else None

        # メッセージ取得
        messages = [msg async for msg in interaction.channel.history(limit=None, oldest_first=True)]
        
        # HTML生成
        html_str = generate_html_transcript(
            interaction.channel.name,
            str(owner) if owner else owner_id,
            str(self.claimed_by) if self.claimed_by else "未担当",
            str(interaction.user),
            messages,
            reason
        )
        
        file_bytes = io.BytesIO(html_str.encode("utf-8"))
        filename = f"transcript-{interaction.channel.name}.html"

        log_embed = discord.Embed(title="📑 Ticket Transcript", description=f"チケット `{interaction.channel.name}` が終了しました。", color=discord.Color.dark_gray())
        log_embed.add_field(name="理由", value=reason, inline=False)

        # 作成者とスタッフ（自分）へDM送信
        for target in [interaction.user, owner]:
            if target:
                try:
                    file_bytes.seek(0)
                    await target.send(embed=log_embed, file=discord.File(io.BytesIO(file_bytes.read()), filename=filename))
                except: pass

        # チャンネル削除
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

        embed = discord.Embed(title="🎟 お問い合わせを受け付けました", description=f"スタッフが来るまでお待ちください。\n{user.mention} 様のサポートを行います。", color=discord.Color.green())
        await channel.send(content=f"{role.mention if role else ''} {user.mention}", embed=embed, view=TicketActionView(self.staff_role_id))
        await interaction.response.send_message(f"✅ チケットを作成しました: {channel.mention}", ephemeral=True)

# =====================
# COG / SETUP
# =====================
class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket_panel", description="チケット作成パネルを設置")
    async def ticket_panel(self, interaction: discord.Interaction, channel: discord.TextChannel, staff_role: discord.Role, title: str = "🎫 サポートチケット", description: str = "お問い合わせは下のボタンから"):
        embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
        msg = await channel.send(embed=embed, view=TicketView(staff_role.id))
        data = load_json(DATA_FILE)
        data[str(msg.id)] = {"guild_id": interaction.guild.id, "staff_role_id": staff_role.id}
        save_json(DATA_FILE, data)
        await interaction.response.send_message("✅ パネルを設置しました。", ephemeral=True)

async def setup(bot):
    data = load_json(DATA_FILE)
    for panel in data.values():
        role_id = panel.get("staff_role_id")
        if role_id:
            bot.add_view(TicketView(role_id))
            bot.add_view(TicketActionView(role_id))
    await bot.add_cog(TicketCog(bot))
