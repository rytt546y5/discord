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
        self.claimed_by = None

    @discord.ui.button(label="🤝 対応する (Claim)", style=discord.ButtonStyle.primary, custom_id="ticket_claim_v2")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(self.staff_role_id)
        if not (role in interaction.user.roles or interaction.user.guild_permissions.manage_channels):
            return await interaction.response.send_message("❌ スタッフのみが対応可能です。", ephemeral=True)

        self.claimed_by = interaction.user
        user_id_match = re.search(r"ticket-(\d+)", interaction.channel.name)
        user_mention = f"<@{user_id_match.group(1)}>" if user_id_match else "お客様"

        embed = discord.Embed(
            title="🤝 担当者が決まりました",
            description=f"{interaction.user.mention} がこのチケットを担当します。",
            color=discord.Color.blue()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        
        self.remove_item(button)
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(content=f"{user_mention}", embed=embed)

    @discord.ui.button(label="🔒 閉じる (Close)", style=discord.ButtonStyle.red, custom_id="ticket_close_v2")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 権限チェック
        if not (interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_channels):
            return await interaction.response.send_message("❌ 権限がありません。", ephemeral=True)

        # 1. まず応答を返す（タイムアウト防止）
        await interaction.response.send_message("⌛ ログを作成してクローズしています...", ephemeral=True)

        # 2. ログの生成を試みる
        log_content = f"--- Ticket Transcript: {interaction.channel.name} ---\n"
        log_content += f"Generated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # チケット作成者の特定
        user_id_match = re.search(r"ticket-(\d+)", interaction.channel.name)
        owner_id = user_id_match.group(1) if user_id_match else None
        owner = interaction.guild.get_member(int(owner_id)) if owner_id else None
        
        log_content += f"Ticket Owner: {owner if owner else owner_id}\n"
        log_content += f"Claimed by  : {self.claimed_by if self.claimed_by else 'None'}\n"
        log_content += f"Closed by   : {interaction.user}\n"
        log_content += "-" * 40 + "\n\n"

        try:
            async for message in interaction.channel.history(limit=None, oldest_first=True):
                t = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                log_content += f"[{t}] {message.author}: {message.clean_content}\n"
                if message.attachments:
                    for att in message.attachments:
                        log_content += f" > Attachment: {att.url}\n"
        except Exception as e:
            log_content += f"\n[!] 履歴の一部取得に失敗しました: {e}\n"

        # バイトデータに変換
        log_file_bytes = log_content.encode("utf-8")

        # 3. ログの送信（失敗しても次の削除へ進む）
        config = load_json(CONFIG_FILE)
        log_chan_id = config.get(str(interaction.guild.id), {}).get("log_channel")

        embed = discord.Embed(
            title="📑 チケットログ保存",
            description=f"チケット `{interaction.channel.name}` が終了しました。",
            color=discord.Color.dark_gray(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="作成者", value=f"<@{owner_id}>" if owner_id else "不明")
        embed.add_field(name="担当者", value=self.claimed_by.mention if self.claimed_by else "なし")

        # 送信先1: ログチャンネル
        if log_chan_id:
            try:
                chan = interaction.guild.get_channel(int(log_chan_id))
                if chan:
                    await chan.send(embed=embed, file=discord.File(io.BytesIO(log_file_bytes), filename=f"log-{interaction.channel.name}.txt"))
            except Exception as e:
                print(f"Log Channel Send Error: {e}")

        # 送信先2: スタッフ（実行者）DM
        try:
            await interaction.user.send(embed=embed, file=discord.File(io.BytesIO(log_file_bytes), filename=f"log-{interaction.channel.name}.txt"))
        except Exception as e:
            print(f"Staff DM Send Error: {e}")

        # 送信先3: チケット作成者DM
        if owner:
            try:
                await owner.send(content="チケットの履歴です。ご利用ありがとうございました。", embed=embed, file=discord.File(io.BytesIO(log_file_bytes), filename=f"log-{interaction.channel.name}.txt"))
            except Exception as e:
                print(f"Owner DM Send Error: {e}")

        # 4. 最後にチャンネルを削除（これだけは絶対にやる）
        try:
            await interaction.channel.delete(reason="Ticket Closed")
        except discord.Forbidden:
            await interaction.followup.send("❌ チャンネル削除権限がありません。Botに『チャンネルの管理』権限を与えてください。", ephemeral=True)
        except Exception as e:
            print(f"Delete Error: {e}")

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
