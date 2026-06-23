import discord
from discord.ext import commands
from discord import app_commands
import json
import os

FILE = "status_data.json"


# =====================
# DATA
# =====================

def load():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


STATUS_EMOJI = {
    "green": "🟢",
    "yellow": "🟡",
    "red": "🔴"
}


# =====================
# USER VIEW（確認用）
# =====================

class StatusView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔍 確認",
        style=discord.ButtonStyle.primary,
        custom_id="status_check_btn"
    )
    async def check(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = load()
        gid = str(interaction.guild.id)

        if gid not in data:
            return await interaction.response.send_message(
                "❌ ステータス未設定",
                ephemeral=True
            )

        s = data[gid]

        embed = discord.Embed(
            title="📌 対応ステータス",
            description=f"{STATUS_EMOJI.get(s.get('status', 'red'))} 現在の状況",
            color=discord.Color.gold()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# =====================
# ADMIN SELECT
# =====================

class StatusSelect(discord.ui.Select):
    def __init__(self):

        options = [
            discord.SelectOption(label="対応可能", value="green", emoji="🟢"),
            discord.SelectOption(label="対応遅延", value="yellow", emoji="🟡"),
            discord.SelectOption(label="対応不可", value="red", emoji="🔴"),
        ]

        super().__init__(
            placeholder="ステータスを変更してください",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="status_select_menu"
        )

    async def callback(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ 管理者のみ変更可能です",
                ephemeral=True
            )

        data = load()
        gid = str(interaction.guild.id)

        data[gid] = {
            "status": self.values[0]
        }

        save(data)

        await interaction.response.send_message(
            f"✅ ステータス更新: {STATUS_EMOJI[self.values[0]]}",
            ephemeral=True
        )


class StatusAdminView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StatusSelect())


# =====================
# COG
# =====================

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # ユーザー用パネル
    # =====================

    @app_commands.command(
        name="status_panel",
        description="ユーザー向けステータス確認パネルを設置します"
    )
    async def status_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        embed = discord.Embed(
            title="📌 ステータスパネル",
            description="🔍 ボタンを押すと現在の状況を確認できます",
            color=discord.Color.blurple()
        )

        await channel.send(
            embed=embed,
            view=StatusView()
        )

        await interaction.response.send_message(
            "✅ ユーザーパネル設置完了",
            ephemeral=True
        )

    # =====================
    # 管理者用パネル
    # =====================

    @app_commands.command(
        name="status_admin",
        description="管理者用ステータス変更パネルを設置します"
    )
    @app_commands.default_permissions(administrator=True)
    async def status_admin(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        embed = discord.Embed(
            title="🛠 ステータス管理パネル",
            description="下から現在のステータスを変更できます",
            color=discord.Color.red()
        )

        await channel.send(
            embed=embed,
            view=StatusAdminView()
        )

        await interaction.response.send_message(
            "✅ 管理パネル設置完了",
            ephemeral=True
        )


# =====================
# SETUP（永続対応）
# =====================

async def setup(bot):
    await bot.add_cog(Status(bot))
    bot.add_view(StatusView())
    bot.add_view(StatusAdminView())
