import discord
from discord.ext import commands
from discord import app_commands
import json
import os


# =========================
# 📦 保存
# =========================
STATUS_FILE = "status.json"


def load_status():
    if not os.path.exists(STATUS_FILE):
        return {}
    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_status(data):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =========================
# 🎛 View
# =========================
class StatusView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def update_panel(self, interaction: discord.Interaction, status: str):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ 管理者のみ使用できます",
                ephemeral=True
            )

        data = load_status()
        guild_id = str(interaction.guild.id)

        data[guild_id] = {
            "status": status,
            "user_id": interaction.user.id
        }

        save_status(data)

        color_map = {
            "green": discord.Color.green(),
            "yellow": discord.Color.gold(),
            "red": discord.Color.red()
        }

        text_map = {
            "green": "🟢 対応中",
            "yellow": "🟡 離席中",
            "red": "🔴 対応不可"
        }

        embed = discord.Embed(
            title="対応ステータス",
            description=f"{text_map[status]}\n\n更新者: {interaction.user.mention}",
            color=color_map[status]
        )

        # 💥ここが修正ポイント（message_id完全排除）
        await interaction.message.edit(embed=embed, view=self)

        await interaction.response.send_message(
            "✅ 更新しました",
            ephemeral=True
        )

    # -------------------------
    # 🟢 対応中
    # -------------------------
    @discord.ui.button(
        label="🟢 対応中",
        style=discord.ButtonStyle.green,
        custom_id="status_green"
    )
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_panel(interaction, "green")

    # -------------------------
    # 🟡 離席中
    # -------------------------
    @discord.ui.button(
        label="🟡 離席中",
        style=discord.ButtonStyle.secondary,
        custom_id="status_yellow"
    )
    async def yellow(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_panel(interaction, "yellow")

    # -------------------------
    # 🔴 対応不可
    # -------------------------
    @discord.ui.button(
        label="🔴 対応不可",
        style=discord.ButtonStyle.red,
        custom_id="status_red"
    )
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_panel(interaction, "red")


# =========================
# 📦 Cog本体
# =========================
class StatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # 📌 パネル設置
    # -------------------------
    @app_commands.command(
        name="status_panel",
        description="対応ステータスパネルを設置します"
    )
    @app_commands.default_permissions(administrator=True)
    async def panel(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        channel: discord.TextChannel
    ):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )

        msg = await channel.send(embed=embed, view=StatusView())

        # 初期状態保存（message_id不要に変更）
        data = load_status()
        data[str(interaction.guild.id)] = {
            "status": "green",
            "message_id": msg.id  # ←履歴用（実運用には使わない）
        }
        save_status(data)

        await interaction.response.send_message(
            "✅ 設置完了",
            ephemeral=True
        )

    # =========================
    # 🔁 再起動時復元
    # =========================
    @commands.Cog.listener()
    async def on_ready(self):
        # persistent view登録（ボタン生存用）
        self.bot.add_view(StatusView())


# =========================
# 🔧 setup
# =========================
async def setup(bot):
    await bot.add_cog(StatusCog(bot))
