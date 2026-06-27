import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re
import io

# =====================
# DATA
# =====================

DATA_FILE = "ticket_data.json"
CONFIG_FILE = "ticket_config.json"

def load_json(file):
    if not os.path.exists(file): return {}
    with open(file, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =====================
# VIEW（チケット内の操作パネル）
# =====================

class TicketActionView(discord.ui.View):
    def __init__(self, staff_role_id: int):
        super().__init__(timeout=None)
        self.staff_role_id = staff_role_id
        self.claimed_by = None # 誰が担当したかを保持

    @discord.ui.button(label="🤝 対応する (Claim)", style=discord.ButtonStyle.primary, custom_id="ticket_claim_v2")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(self.staff_role_id)
        is_staff = role in interaction.user.roles if role else False
        is_admin = interaction.user.guild_permissions.manage_channels

        if not (is_staff or is_admin):
            return await interaction.response.send_message("❌ スタッフのみが対応可能です。", ephemeral=True)

        self.claimed_by = interaction.user # 担当者をセット
        
        user_id_match = re.search(r"ticket-(\d+)", interaction.channel.name)
        user_mention = f"<@{user_id_match.group(1)}>" if user_id_match else "お客様"

        embed = discord.Embed(
            title="🤝 担当者が決まりました",
            description=f"{interaction.user.mention} がこのチケットを担当します。\nこれ以降のご案内は担当スタッフより行います。",
            color=discord.Color.blue()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"Ticket ID: {interaction.channel.id}")

        self.remove_item(button) # ボタンを消す
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(content=f"{user_mention}", embed=embed)

    @discord.ui.button(label="🔒 閉じる (Close)", style=discord.ButtonStyle.red, custom_id="ticket_close_v2")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not (interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_channels):
            return await interaction.response.send_message("❌ 権限がありません。", ephemeral=True)

        await interaction.response.send_message("⌛ ログを生成してクローズしています...", ephemeral=True)

        # === Transcript (履歴) の生成 ===
        user_id_match = re.search(r"ticket-(\d+)", interaction.channel.name)
        owner_id = user_id_match.group(1) if user_id_match else "不明"
        owner_member = interaction.guild.get_member(int(owner_id)) if owner_id.isdigit() else None
        owner_name = f"{owner_member} ({owner_id})" if owner_member else owner_id

        transcript = f"--- Ticket Transcript ---\n"
        transcript += f"Ticket Name: {interaction.channel.name}\n"
        transcript += f"Opened by  : {owner_name}\n"
        transcript += f"Claimed by : {self.claimed_by if self.claimed_by else 'なし'}\n"
        transcript += f"Closed by  : {interaction.user} ({interaction.user.id})\n"
        transcript += f"Closed at  : {interaction.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        transcript += "-" * 40 + "\n\n"

        async for message in interaction.channel.history(limit=None, oldest_first=True):
            time_str = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            content = message.content if message.content else "[画像/埋め込み]"
            transcript += f"[{time_str}] {message.author}: {content}\n"
            if message.attachments:
                for att in message.attachments:
                    transcript += f" > Attachment: {att.url}\n"

        file_data = io.BytesIO(transcript.encode("utf-8"))
        filename = f"transcript-{interaction.channel.name}.txt"

        # 共通ログEmbed
        log_embed = discord.Embed(
            title="📑 チケット履歴保存",
            description=f"チケット `{interaction.channel.name}` が正常にクローズされました。",
            color=discord.Color.from_rgb(47, 49, 54) # Tickets v2っぽいダークカラー
        )
        log_embed.add_field(name="作成者", value=f"<@{owner_id}>", inline=True)
        log_embed.add_field(name="担当者", value=f"{self.claimed_by.mention if self.claimed_by else 'なし'}", inline=True)
        log_embed.add_field(name="削除者", value=interaction.user.mention, inline=True)
        log_embed.set_footer(text="Ticket Transcript System")

        # 1. ログチャンネルへ送信
        config = load_json(CONFIG_FILE)
        log_channel_id = config.get(str(interaction.guild.id), {}).get("log_channel")
        if log_channel_id:
            log_chan = interaction.guild.get_channel(log_channel_id)
            if log_chan:
                file_data.seek(0)
                await log_chan.send(embed=log_embed, file=discord.File(file_data, filename=filename))

        # 2. スタッフ（削除者）のDMへ送信
        try:
            file_data.seek(0)
            await interaction.user.send(embed=log_embed, file=discord.File(file_data, filename=filename))
        except: pass

        # 3. チケット作成者のDMへ送信 (Tickets v2 仕様)
        if owner_member:
            try:
                file_data.seek(0)
                await owner_member.send(
                    content=f"ご利用ありがとうございました。チケット `{interaction.channel.name}` の履歴です。",
                    embed=log_embed, 
                    file=discord.File(file_data, filename=filename)
                )
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
        if existing:
            return await interaction.response.send_message(f"❌ 既にチケットが開かれています: {existing.mention}", ephemeral=True)

        channel = await guild.create_text_channel(name=f"ticket-{user.id}")
        await channel.set_permissions(guild.default_role, view_channel=False)
        await channel.set_permissions(user, view_channel=True, send_messages=True)

        role = guild.get_role(self.staff_role_id)
        if role:
            await channel.set_permissions(role, view_channel=True, send_messages=True)

        embed = discord.Embed(
            title="🎟 お問い合わせを受け付けました",
            description=f"担当スタッフが来るまで、ご用件を具体的にお書きください。\n{user.mention} 様のサポートを全力で行います。",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="通知", value=f"{role.mention if role else 'スタッフ'} に通知されました", inline=False)

        await channel.send(
            content=f"{role.mention if role else ''} {user.mention}",
            embed=embed,
            view=TicketActionView(self.staff_role_id)
        )
        await interaction.response.send_message(f"✅ チケットを作成しました: {channel.mention}", ephemeral=True)

# =====================
# COG / SETUP
# =====================

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket_log_set", description="チケットのログ（履歴）送信先を設定します")
    async def ticket_log_set(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = load_json(CONFIG_FILE)
        config[str(interaction.guild.id)] = {"log_channel": channel.id}
        save_json(CONFIG_FILE, config)
        await interaction.response.send_message(f"✅ チケットログの送信先を {channel.mention} に設定しました。", ephemeral=True)

    @app_commands.command(name="ticket_panel", description="チケット作成パネルを設置します")
    async def ticket_panel(self, interaction: discord.Interaction, channel: discord.TextChannel, staff_role: discord.Role, title: str = "🎫 サポートチケット", description: str = "お問い合わせが必要な場合は、下のボタンを押してください。"):
        embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
        embed.set_footer(text="Tickets System | Provided by Mero")
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
