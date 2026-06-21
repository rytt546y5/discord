import discord
from discord.ext import commands
from discord import app_commands


# =====================
# BUTTON
# =====================
class RoleButton(discord.ui.Button):
    def __init__(self, role: discord.Role):
        super().__init__(
            label=role.name,
            style=discord.ButtonStyle.primary,
            custom_id=f"role_{role.id}"
        )
        self.role = role

    async def callback(self, interaction: discord.Interaction):

        # 既に持ってるか判定
        if self.role in interaction.user.roles:
            await interaction.user.remove_roles(self.role)
            return await interaction.response.send_message(
                f"❌ {self.role.name} を解除しました",
                ephemeral=True
            )

        await interaction.user.add_roles(self.role)
        await interaction.response.send_message(
            f"✅ {self.role.name} を付与しました",
            ephemeral=True
        )


# =====================
# VIEW
# =====================
class RolePanelView(discord.ui.View):
    def __init__(self, roles: list[discord.Role]):
        super().__init__(timeout=None)

        self.roles = roles[:5]  # 最大5

        for role in self.roles:
            self.add_item(RoleButton(role))


# =====================
# COG
# =====================
class RolePanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="role_panel",
        description="ロール配布パネルを作成（最大5）"
    )
    @app_commands.describe(
        channel="設置するチャンネル",
        role1="ロール1",
        role2="ロール2（任意）",
        role3="ロール3（任意）",
        role4="ロール4（任意）",
        role5="ロール5（任意）",
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

        roles = [role1, role2, role3, role4, role5]
        roles = [r for r in roles if r is not None]

        if len(roles) == 0:
            return await interaction.response.send_message(
                "❌ ロールが指定されていません",
                ephemeral=True
            )

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.gold()
        )

        role_list_text = "\n".join([f"• {r.name}" for r in roles])

        embed.add_field(
            name="📌 対象ロール",
            value=role_list_text,
            inline=False
        )

        await channel.send(
            embed=embed,
            view=RolePanelView(roles)
        )

        await interaction.response.send_message(
            "✅ ロールパネル設置完了",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(RolePanel(bot))
