import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio


class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = set()

    @discord.ui.button(label="🎉 参加する", style=discord.ButtonStyle.green, custom_id="giveaway_join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):

        user_id = interaction.user.id

        if user_id in self.participants:
            return await interaction.response.send_message(
                "すでに参加済みです",
                ephemeral=True
            )

        self.participants.add(user_id)

        await interaction.response.send_message(
            "🎉 参加しました！",
            ephemeral=True
        )


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="giveaway", description="抽選イベントを作成")
    @app_commands.default_permissions(administrator=True)
    async def giveaway(
        self,
        interaction: discord.Interaction,
        title: str,
        prize: str,
        winner_count: int = 1
    ):

        embed = discord.Embed(
            title=f"🎉 {title}",
            description=f"賞品: {prize}\n\nボタンから参加できます！",
            color=discord.Color.gold()
        )

        view = GiveawayView()

        await interaction.channel.send(embed=embed, view=view)

        await interaction.response.send_message("🎉 Giveaway作成完了", ephemeral=True)

        # 終了コマンド用にview保持
        self.current_view = view
        self.current_message = None

    @app_commands.command(name="giveaway_end", description="抽選を終了して当選者を決定")
    @app_commands.default_permissions(administrator=True)
    async def end(self, interaction: discord.Interaction):

        view = getattr(self, "current_view", None)

        if not view or len(view.participants) == 0:
            return await interaction.response.send_message(
                "参加者がいません",
                ephemeral=True
            )

        winners = random.sample(
            list(view.participants),
            k=min(1, len(view.participants))
        )

        winner_mentions = [f"<@{w}>" for w in winners]

        embed = discord.Embed(
            title="🎉 Giveaway結果",
            description=f"当選者: {', '.join(winner_mentions)}",
            color=discord.Color.green()
        )

        await interaction.channel.send(embed=embed)

        await interaction.response.send_message("抽選終了", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Giveaway(bot))
