import discord
from discord.ext import commands
from discord import app_commands


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def make_embed(self, title, desc, commands):
        embed = discord.Embed(
            title=title,
            description=desc,
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="📌 コマンド一覧",
            value="\n".join(commands),
            inline=False
        )

        return embed

    # =====================
    # サポート系
    # =====================
    @discord.ui.button(label="🎟 サポート", style=discord.ButtonStyle.green)
    async def support(self, interaction: discord.Interaction, button: discord.ui.Button):

        cmds = [
            "/ticket_panel",
            "/status",
            "/verify_panel"
        ]

        await interaction.response.edit_message(
            embed=self.make_embed("🎟 サポート系", "問い合わせ・認証関連", cmds),
            view=self
        )

    # =====================
    # 自販機系（最重要）
    # =====================
    @discord.ui.button(label="🥤 自販機", style=discord.ButtonStyle.blurple)
    async def vending(self, interaction: discord.Interaction, button: discord.ui.Button):

        cmds = [
            "自販機作成",
            "自販機設置",
            "自販機削除",
            "商品追加",
            "商品削除",
            "商品情報変更",
            "在庫追加",
            "在庫引出",
            "在庫確認",
            "パネル更新",
            "ロール付与設定",
            "クーポン作成",
            "クーポン削除",
            "クーポン一覧",
            "許可ユーザー管理",
            "非公開ログ",
            "公開ログ"
        ]

        await interaction.response.edit_message(
            embed=self.make_embed("🥤 自販機系", "販売・在庫・ロール管理", cmds),
            view=self
        )

    # =====================
    # イベント系
    # =====================
    @discord.ui.button(label="🎉 イベント", style=discord.ButtonStyle.gray)
    async def event(self, interaction: discord.Interaction, button: discord.ui.Button):

        cmds = [
            "/giveaway_panel",
            "/giveaway_pick",
            "/poll"
        ]

        await interaction.response.edit_message(
            embed=self.make_embed("🎉 イベント系", "抽選・投票", cmds),
            view=self
        )

    # =====================
    # 管理系
    # =====================
    @discord.ui.button(label="⚙ 管理", style=discord.ButtonStyle.red)
    async def admin(self, interaction: discord.Interaction, button: discord.ui.Button):

        cmds = [
            "/purge",
            "/nuke",
            "/serverinfo",
            "/roleall_add",
            "/roleall_remove",
            "/ngword_add",
            "/ngword_remove"
        ]

        await interaction.response.edit_message(
            embed=self.make_embed("⚙ 管理系", "サーバー管理機能", cmds),
            view=self
        )

    # =====================
    # ログ系
    # =====================
    @discord.ui.button(label="📡 ログ", style=discord.ButtonStyle.secondary)
    async def log(self, interaction: discord.Interaction, button: discord.ui.Button):

        cmds = [
            "/join_log",
            "/set_leave_log"
        ]

        await interaction.response.edit_message(
            embed=self.make_embed("📡 ログ系", "入退室ログ関連", cmds),
            view=self
        )


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="全機能ダッシュボード"
    )
    async def help(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="📖 Bot Dashboard",
            description="下のボタンで機能カテゴリを選択してください",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed,
            view=HelpView(),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Help(bot))
