import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "role_panel.json"


# =====================
# DATA
# =====================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# =====================
# BUTTON
# =====================

class RoleButton(discord.ui.Button):
    def __init__(self, role_id: int):
        super().__init__(
            label=f"Role {role_id}",
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


# =====================
# VIEW
# =====================

class RolePanelView(discord.ui.View):
    def __init__(self, role_ids: list[int]):
        super().__init__(timeout=None)

        for rid in role_ids[:5]:
            self.add_item(RoleButton(rid))


# =====================
# COG
# =====================

class RolePanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="role_panel",
        description="ロールパネル作成"
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
        description: str = "ボタンでロールを付与/解除"
    ):

        roles = [role1, role2, role3, role4, role5]
        roles = [r for r in roles if r is not None]

        role_ids = [r.id for r in roles]

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.gold()
        )

        embed.add_field(
            name="📌 対象ロール",
            value="\n".join([f"• {r.name}" for r in roles]),
            inline=False
        )

        msg = await channel.send(
            embed=embed,
            view=RolePanelView(role_ids)
        )

        # 保存（重要）
        data = load_data()

        data[str(msg.id)] = {
            "guild_id": interaction.guild.id,
            "roles": role_ids
        }

        save_data(data)

        await interaction.response.send_message(
            "✅ ロールパネル設置完了",
            ephemeral=True
        )


# =====================
# SETUP（復元）
# =====================

async def setup(bot):

    data = load_data()

    for panel in data.values():

        role_ids = panel.get("roles", [])

        if not role_ids:
            continue

        bot.add_view(
            RolePanelView(role_ids)
        )

    await bot.add_cog(RolePanel(bot))
