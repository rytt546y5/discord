import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import timedelta
import datetime

NGWORDS_FILE = "ngwords.json"
VIOLATIONS_FILE = "violations.json"
NG_CONFIG_FILE = "ng_config.json" # ロール設定保存用

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =====================
# VIEW (警告パネルのボタン)
# =====================
class NgViolationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅解除✅", style=discord.ButtonStyle.success, custom_id="ng_unmute_v2")
    async def unmute(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ 管理者のみ可能です。", ephemeral=True)

        if not interaction.message.mentions:
            return await interaction.response.send_message("❌ ユーザーを特定できませんでした。", ephemeral=True)
        
        target_user = interaction.message.mentions[0]
        member = interaction.guild.get_member(target_user.id)

        if member:
            try:
                await member.timeout(None, reason=f"管理者 {interaction.user} による解除")
                await interaction.response.send_message(f"✅ {member.mention} のタイムアウトを解除しました。", ephemeral=True)
                await interaction.message.edit(view=None)
            except Exception as e:
                await interaction.response.send_message(f"❌ 解除失敗: {e}", ephemeral=True)

    @discord.ui.button(label="⚠️BAN⚠️", style=discord.ButtonStyle.danger, custom_id="ng_ban_v2")
    async def ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ 管理者のみ可能です。", ephemeral=True)

        if not interaction.message.mentions:
            return await interaction.response.send_message("❌ ユーザーを特定できませんでした。", ephemeral=True)

        target_user = interaction.message.mentions[0]
        try:
            await interaction.guild.ban(target_user, reason=f"NGワード違反累積によるBAN")
            await interaction.response.send_message(f"✅ {target_user} をサーバーから追放しました。", ephemeral=True)
            await interaction.message.edit(view=None)
        except Exception as e:
            await interaction.response.send_message(f"❌ BAN失敗: {e}", ephemeral=True)

# =====================
# COG
# =====================
class NgWordCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ngwords = load_json(NGWORDS_FILE, [])
        self.violations = load_json(VIOLATIONS_FILE, {})
        self.timeout_durations = [
            timedelta(minutes=1),
            timedelta(minutes=10),
            timedelta(minutes=30),
            timedelta(hours=1),
            timedelta(hours=3)
        ]

    async def apply_violation(self, message: discord.Message):
        uid = str(message.author.id)
        gid = str(message.guild.id)
        
        # 回数加算
        self.violations[uid] = self.violations.get(uid, 0) + 1
        save_json(VIOLATIONS_FILE, self.violations)
        count = self.violations[uid]

        # タイムアウト時間の決定
        index = min(count - 1, len(self.timeout_durations) - 1)
        duration = self.timeout_durations[index]

        # 1. タイムアウト実行
        try:
            await message.author.timeout(duration, reason=f"NGワード違反 ({count}回目)")
        except: pass

        # 2. 警告ロールの付与 (3回目以降)
        role_added_msg = ""
        if count >= 3:
            config = load_json(NG_CONFIG_FILE, {})
            role_id = config.get(gid, {}).get("violation_role_id")
            if role_id:
                role = message.guild.get_role(int(role_id))
                if role and role not in message.author.roles:
                    try:
                        await message.author.add_roles(role, reason="NGワード違反累積によるロール付与")
                        role_added_msg = f"\n⚠️ 累積違反のため **{role.name}** ロールを付与しました。"
                    except: pass

        # 3. 警告パネル送信
        duration_text = f"{int(duration.total_seconds() // 60)}分" if duration < timedelta(hours=1) else f"{int(duration.total_seconds() // 3600)}時間"
        
        embed = discord.Embed(
            title="🛑 違反行為を検知しました",
            description=f"{message.author.mention} をタイムアウトしました。\n{role_added_msg}",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.add_field(name="制限内容", value=f"**{duration_text}** のタイムアウト", inline=True)
        embed.add_field(name="累計違反", value=f"{count} 回", inline=True)
        embed.set_footer(text="管理者は以下のボタンから操作可能です。")

        await message.channel.send(content=message.author.mention, embed=embed, view=NgViolationView())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        if message.author.guild_permissions.administrator: return

        content = message.content.lower()
        for w in self.ngwords:
            if w.lower() in content:
                try: await message.delete()
                except: pass
                await self.apply_violation(message)
                return

    @app_commands.command(name="ngword_add", description="NGワードを追加")
    @app_commands.default_permissions(administrator=True)
    async def add(self, interaction: discord.Interaction, word: str):
        if word not in self.ngwords:
            self.ngwords.append(word)
            save_json(NGWORDS_FILE, self.ngwords)
        await interaction.response.send_message(f"✅ 「{word}」を追加しました。", ephemeral=True)

    @app_commands.command(name="ngword_role_set", description="3回以上違反したユーザーに付与するロールを設定します")
    @app_commands.describe(role="付与する警告ロール")
    @app_commands.default_permissions(administrator=True)
    async def role_set(self, interaction: discord.Interaction, role: discord.Role):
        config = load_json(NG_CONFIG_FILE, {})
        gid = str(interaction.guild.id)
        if gid not in config: config[gid] = {}
        config[gid]["violation_role_id"] = role.id
        save_json(NG_CONFIG_FILE, config)
        await interaction.response.send_message(f"✅ 警告ロールを {role.mention} に設定しました（3回目以降の違反で付与されます）。", ephemeral=True)

    @app_commands.command(name="ngword_list", description="NGワード一覧を表示")
    @app_commands.default_permissions(administrator=True)
    async def list_words(self, interaction: discord.Interaction):
        text = "\n".join(self.ngwords) if self.ngwords else "なし"
        await interaction.response.send_message(f"🚫 **登録済みワード**:\n{text}", ephemeral=True)

async def setup(bot):
    bot.add_view(NgViolationView())
    await bot.add_cog(NgWordCog(bot))
