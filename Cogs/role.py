import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = “role_panel_config.json”

=====================

DATA

=====================

def load_data():
if not os.path.exists(DATA_FILE):
return {}

with open(DATA_FILE, "r", encoding="utf-8") as f:
    return json.load(f)

def save_data(data):
with open(DATA_FILE, “w”, encoding=“utf-8”) as f:
json.dump(
data,
f,
indent=2,
ensure_ascii=False
)

=====================

BUTTON

=====================

class RoleButton(discord.ui.Button):
def init(self, role_id: int, role_name: str):

    super().__init__(
        label=role_name,
        style=discord.ButtonStyle.primary,
        custom_id=f"role_{role_id}"
    )
    self.role_id = role_id
async def callback(self, interaction: discord.Interaction):
    role = interaction.guild.get_role(self.role_id)
    if role is None:
        return await interaction.response.send_message(
            "❌ ロールが見つかりません",
            ephemeral=True
        )
    member = interaction.user
    if not interaction.guild.me.guild_permissions.manage_roles:
        return await interaction.response.send_message(
            "❌ Botにロール管理権限がありません",
            ephemeral=True
        )
    try:
        if role in member.roles:
            await member.remove_roles(role)
            return await interaction.response.send_message(
                f"❌ {role.name} を解除しました",
                ephemeral=True
            )
        await member.add_roles(role)
        await interaction.response.send_message(
            f"✅ {role.name} を付与しました",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ ロール階層が原因で操作できません",
            ephemeral=True
        )

=====================

VIEW

=====================

class RolePanelView(discord.ui.View):
def init(self, roles):

    super().__init__(timeout=None)
    for role_id, role_name in roles[:5]:
        self.add_item(
            RoleButton(role_id, role_name)
        )

=====================

COG

=====================

class RolePanel(commands.Cog):
def init(self, bot):
self.bot = bot

@app_commands.command(
    name="role_panel",
    description="ロール配布パネルを作成（最大5）"
)
@app_commands.describe(
    channel="設置するチャンネル",
    role1="ロール1",
    role2="ロール2",
    role3="ロール3",
    role4="ロール4",
    role5="ロール5",
    title="パネルタイトル",
    description="説明文"
)
async def role_panel(
    self,
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    role1: discord.Role,
    role2: discord.Role = None,
    role3: discord.Role = None,
    role4: discord.Role = None,
    role5: discord.Role = None,
    title: str = "🎭 ロールパネル",
    description: str = "ボタンでロールを付与/解除できます"
):
    roles = [
        role1,
        role2,
        role3,
        role4,
        role5
    ]
    roles = [
        r for r in roles
        if r is not None
    ]
    if not roles:
        return await interaction.response.send_message(
            "❌ ロールが指定されていません",
            ephemeral=True
        )
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.gold()
    )
    embed.add_field(
        name="📌 対象ロール",
        value="\n".join(
            [f"• {r.name}" for r in roles]
        ),
        inline=False
    )
    role_data = [
        (r.id, r.name)
        for r in roles
    ]
    msg = await channel.send(
        embed=embed,
        view=RolePanelView(role_data)
    )
    data = load_data()
    data[str(msg.channel.id)] = {
        "roles": role_data
    }
    save_data(data)
    await interaction.response.send_message(
        "✅ ロールパネル設置完了",
        ephemeral=True
    )

=====================

SETUP

=====================

async def setup(bot):
await bot.add_cog(
RolePanel(bot)
)
