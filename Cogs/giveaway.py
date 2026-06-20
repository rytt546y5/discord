import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from datetime import datetime, timedelta


class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = set()

    @discord.ui.button(label="🎉 参加する", style=discord.ButtonStyle.green, custom_id="giveaway_join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id in self.participants:
            return await interaction.response.send_message(
                "すでに参加済みです",
                ephemeral=True
            )

        self.participants.add(interaction.user.id)

        await interaction.response.send_message(
            "🎉 参加しました！",
            ephemeral=True
        )


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaway = None  # 現在の抽選

    @app_commands.command(name="giveaway", description="Giveaway作成（時間付き）")
    @app_commands.default_permissions(administrator=True)
    async def giveaway(
        self,
        interaction: discord.Interaction,
        title: str,
        prize: str,
        minutes: int = 0,
        winner_count: int = 1
    ):

        view = GiveawayView()

        embed = discord.Embed(
            title=f"🎉 {title}",
            description=(
                f"🎁 報酬: {prize}\n"
                f"👥 参加ボタンを押してください\n"
                f"⏰ 終了時間: {minutes if minutes > 0 else '未設定'}分"
            ),
            color=discord.Color.gold()
        )

        message = await interaction.channel.send(embed=embed, view=view)

        await interaction.response.send_message("Giveaway作成完了", ephemeral=True)

        self.active_giveaway = {
            "message": message,
            "view": view,
            "winner_count": winner_count
        }

        # 時間制限あり
        if minutes > 0:
            await asyncio.sleep(minutes * 60)

            if not self.active_giveaway:
                return

            await self.end_giveaway(interaction.channel)


    @app_commands.command(name="giveaway_end", description="Giveaway終了")
    @app_commands.default_permissions(administrator=True)
    async def giveaway_end(self, interaction: discord.Interaction):
        await self.end_giveaway(interaction.channel)
        await interaction.response.send_message("終了しました", ephemeral=True)


    async def end_giveaway(self, channel: discord.TextChannel):

        if not self.active_giveaway:
            return

        view = self.active_giveaway["view"]
        winner_count = self.active_giveaway["winner_count"]

        if len(view.participants) == 0:
            embed = discord.Embed(
                title="🎉 Giveaway終了",
                description="参加者がいませんでした",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)
            self.active_giveaway = None
            return

        winners = random.sample(
            list(view.participants),
            k=min(winner_count, len(view.participants))
        )

        mentions = [f"<@{w}>" for w in winners]

        embed = discord.Embed(
            title="🎉 Giveaway結果",
            description=f"🏆 当選者: {', '.join(mentions)}",
            color=discord.Color.green()
        )

        await channel.send(embed=embed)

        self.active_giveaway = None


async def setup(bot):
    await bot.add_cog(Giveaway(bot))
