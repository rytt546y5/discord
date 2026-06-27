import discord
from discord.ext import commands
from discord import app_commands

class AdminGuard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ボット全体のコマンドツリーに「検問」を登録
        self.bot.tree.interaction_check = self.global_admin_check

    async def global_admin_check(self, interaction: discord.Interaction) -> bool:
        """
        ボット全体の全コマンドが実行される前に呼ばれるチェック関数
        """
        # 1. 操作が「スラッシュコマンド」であるか判定
        if interaction.type == discord.InteractionType.application_command:
            # 実行者が管理者権限を持っているかチェック
            if interaction.user.guild_permissions.administrator:
                return True # 管理者なら実行許可
            
            # 管理者でない場合は、メッセージを返して実行を阻止
            await interaction.response.send_message(
                "❌ **権限エラー**: スラッシュコマンドは管理者のみが使用可能です。\n一般ユーザーの方はパネルのボタンを使用してください。", 
                ephemeral=True
            )
            return False # 実行を拒否

        # 2. ボタンやセレクトメニュー（コンポーネント）の操作は全員パス
        # これにより、一般ユーザーも「商品受取」や「チケット作成」のボタンは押せます。
        return True

async def setup(bot):
    await bot.add_cog(AdminGuard(bot))
