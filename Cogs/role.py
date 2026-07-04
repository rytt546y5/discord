import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "role_panel.json"

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =====================
# BUTTON
# =====================
class RoleButton(discord.ui.Button):
    def __init__(self, role_id: int, label: str):
        # ラベルが長すぎる場合の対策
        display_label = label[:80] if label else f"Role {role_id}"
        super().__init__(
            label=display_label,
            style=discord.ButtonStyle.primary,
            custom_id=f"role_{role_id}"
        )
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(self.role_id)
        if role is None:
            return await interaction.response.send_message("❌ ロールが見つかりません。削除された可能性があります。", ephemeral=True)

        if role in interaction.user.roles:
            try:
                await interaction.user.remove_roles(role)
                await interaction.response.send_message(f"✅ {role.name} を解除しました", ephemeral=True)
            except:
                await interaction.response.send_message("❌ 権限不足でロールを解除できません。", ephemeral=True)
        else:
            try:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"✅ {role.name} を付与しました", ephemeral=True)
            except:
                await interaction.response.send_message("❌ 権限不足でロールを付与できません。", ephemeral=True)

# =====================
# VIEW
# =====================
class RolePanelView(discord.ui.View):
    def __init__(self, roles_info: list):
        super().__init__(timeout=None)
        for r in roles_info[:5]:
            # データ形式の自動判別（古い形式：int, 新しい形式：dict）
            if isinstance(r, int):
                # 古いデータの場合
                self.add_item(RoleButton(r, f"Role {r}"))
            elif isinstance(r, dict):
                # 新しいデータの場合
                self.add_item(RoleButton(r["id"], r["name"]))

# =====================
# COG
# =====================
class RolePanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="role_panel", description="セルフロールパネルを作成します")
    @app_commands.default_permissions(administrator=True)
    async def role_panel(
        self, interaction: discord.Interaction, channel: discord.TextChannel,
        role1: discord.Role, role2: discord.Role = None, role3: discord.Role = None,
        role4: discord.Role = None, role5: discord.Role = None,
        title: str = "🎭 ロールパネル", description: str = "下のボタンを押してロールを付け外ししてください。"
    ):
        roles = [r for r in [role1, role2, role3, role4, role5] if r is not None]
        roles_info = [{"id": r.id, "name": r.name} for r in roles]

        embed = discord.Embed(title=title, description=description, color=discord.Color.gold())
        embed.add_field(name="📌 対象ロール", value="\n".join([f"• {r.mention}" for r in roles]), inline=False)

        msg = await channel.send(embed=embed, view=RolePanelView(roles_info))

        data = load_data()
        data[str(msg.id)] = {"guild_id": interaction.guild.id, "roles": roles_info}
        save_data(data)

        await interaction.response.send_message("✅ ロールパネルを設置しました。", ephemeral=True)

async def setup(bot):
    data = load_data()
    for msg_id, panel in data.items():
        roles_info = panel.get("roles", [])
        if roles_info:
            # 安全にViewを復元
            bot.add_view(RolePanelView(roles_info))

    await bot.add_cog(RolePanel(bot))
