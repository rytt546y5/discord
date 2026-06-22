import discord
from discord.ext import commands
from discord import app_commands


# =====================
# STATUS PANEL VIEW
# =====================
class StatusPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📌 ステータス確認",
        style=discord.ButtonStyle.primary,
        custom_id="status_open"
    )
    async def open_status(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        embed = discord.Embed(
            title="📌対応ステータス📌",
            color=discord.Color.gold()
        )

        # 🟢正常
        embed.add_field(
            name="🟢 対応済み",
            value="通常通り対応しています",
            inline=False
        )

        # 🟡変更（ここが修正ポイント）
        embed.add_field(
            name="🟡 対応遅延",
            value="一部対応に遅れが発生しています",
            inline=False
        )

        # 🔴停止（必要なら）
        embed.add_field(
            name="🔴 対応停止",
            value="現在対応を停止しています",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# =====================
# COG
# =====================
class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="status_panel",
        description="ステータスパネルを設置"
    )
    @app_commands.default_permissions(administrator=True)
    async def status_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        embed = discord.Embed(
            title="📌対応ステータス📌",
            description="ボタンから最新ステータスを確認できます",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="使い方",
            value="ボタンを押すだけでステータス表示",
            inline=False
        )

        await channel.send(
            embed=embed,
            view=StatusPanelView()
        )

        await interaction.response.send_message(
            "✅ ステータスパネル設置完了",
            ephemeral=True
        )


# =====================
# SETUP
# =====================
async def setup(bot):
    await bot.add_cog(Status(bot))
