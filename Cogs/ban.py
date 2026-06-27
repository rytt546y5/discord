import discord
from discord.ext import commands
from discord import app_commands

class BanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="規約違反ユーザーをBANし、本人とチャンネルに通知します")
    @app_commands.describe(
        user="BANするユーザーを選択してください",
        reason="BANの理由や追加のメッセージを入力してください"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        # 自分のロールより上の役職者はBANできないチェック
        if interaction.user.top_role <= user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ 自分より上の役職を持つユーザーをBANすることはできません。", ephemeral=True)

        if not interaction.guild.me.guild_permissions.ban_members:
            return await interaction.response.send_message("❌ Botに「メンバーをBAN」する権限がありません。", ephemeral=True)

        # === Embed作成 ===
        # タイトル指定: 本規約に違反し @?? をBANしました。
        embed = discord.Embed(
            title=f"本規約に違反し {user.display_name} をBANしました。",
            description=f"**理由・詳細:**\n{reason}",
            color=discord.Color.red(),
            timestamp=interaction.created_at
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"実行者: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        # 1. 本人へのDM送信を試行
        try:
            dm_embed = embed.copy()
            dm_embed.title = f"【通知】{interaction.guild.name} からBANされました"
            await user.send(embed=dm_embed)
            dm_status = "✅ DM送信成功"
        except:
            dm_status = "⚠️ DM送信失敗（閉鎖など）"

        # 2. BANの実行
        try:
            await user.ban(reason=f"実行者: {interaction.user} | 理由: {reason}")
            
            # 3. チャンネルへの送信
            await interaction.response.send_message(content=f"{dm_status}", embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ BANの実行中にエラーが発生しました: {e}", ephemeral=True)

    # 権限エラーのハンドリング
    @ban.error
    async def ban_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ あなたにはメンバーをBANする権限がありません。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BanCog(bot))
