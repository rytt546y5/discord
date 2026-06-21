import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random

class GiveawayView(discord.ui.View):
def init(self):
super().init(timeout=None)
self.participants = set()

@discord.ui.button(
    label="🎉 参加 (0)",
    style=discord.ButtonStyle.green,
    custom_id="giveaway_join"
)
async def join(
    self,
    interaction: discord.Interaction,
    button: discord.ui.Button
):
    if interaction.user.id in self.participants:
        return await interaction.response.send_message(
            "❌ 既に参加しています",
            ephemeral=True
        )
    self.participants.add(interaction.user.id)
    button.label = f"🎉 参加 ({len(self.participants)})"
    await interaction.message.edit(view=self)
    await interaction.response.send_message(
        "✅ Giveawayに参加しました",
        ephemeral=True
    )

class Giveaway(commands.Cog):
def init(self, bot):
self.bot = bot
self.active_giveaways = {}

async def finish_giveaway(self, message_id: int):
    if message_id not in self.active_giveaways:
        return
    data = self.active_giveaways[message_id]
    message = data["message"]
    view = data["view"]
    prize = data["prize"]
    winner_count = data["winner_count"]
    for child in view.children:
        child.disabled = True
    participants = list(view.participants)
    if len(participants) == 0:
        embed = discord.Embed(
            title="🎉 Giveaway終了",
            description="参加者がいませんでした",
            color=discord.Color.red()
        )
        await message.edit(embed=embed, view=view)
        del self.active_giveaways[message_id]
        return
    winner_count = min(
        winner_count,
        len(participants)
    )
    winners = random.sample(
        participants,
        winner_count
    )
    winner_mentions = "\n".join(
        f"<@{winner}>"
        for winner in winners
    )
    embed = discord.Embed(
        title="🎉 Giveaway終了",
        color=discord.Color.gold()
    )
    embed.add_field(
        name="景品",
        value=prize,
        inline=False
    )
    embed.add_field(
        name="当選者",
        value=winner_mentions,
        inline=False
    )
    embed.add_field(
        name="参加人数",
        value=str(len(participants)),
        inline=False
    )
    await message.edit(
        embed=embed,
        view=view
    )
    await message.channel.send(
        f"🎉 おめでとうございます！\n{winner_mentions}"
    )
    del self.active_giveaways[message_id]
@app_commands.command(
    name="giveaway",
    description="Giveawayを作成します"
)
@app_commands.default_permissions(administrator=True)
async def giveaway(
    self,
    interaction: discord.Interaction,
    title: str,
    prize: str,
    minutes: int = 0,
    winner_count: int = 1
):
    await interaction.response.defer(
        ephemeral=True
    )
    view = GiveawayView()
    embed = discord.Embed(
        title=f"🎉 {title}",
        color=discord.Color.gold()
    )
    embed.add_field(
        name="景品",
        value=prize,
        inline=False
    )
    embed.add_field(
        name="当選人数",
        value=str(winner_count),
        inline=False
    )
    embed.add_field(
        name="終了時間",
        value=(
            f"{minutes}分後"
            if minutes > 0
            else "手動終了"
        ),
        inline=False
    )
    message = await interaction.channel.send(
        embed=embed,
        view=view
    )
    self.active_giveaways[message.id] = {
        "message": message,
        "view": view,
        "prize": prize,
        "winner_count": winner_count
    }
    await interaction.followup.send(
        "✅ Giveawayを作成しました",
        ephemeral=True
    )
    if minutes > 0:
        await asyncio.sleep(
            minutes * 60
        )
        await self.finish_giveaway(
            message.id
        )
@app_commands.command(
    name="giveaway_end",
    description="Giveawayを終了します"
)
@app_commands.default_permissions(administrator=True)
async def giveaway_end(
    self,
    interaction: discord.Interaction
):
    if len(self.active_giveaways) == 0:
        return await interaction.response.send_message(
            "❌ 開催中のGiveawayがありません",
            ephemeral=True
        )
    message_id = next(
        iter(self.active_giveaways)
    )
    await self.finish_giveaway(
        message_id
    )
    await interaction.response.send_message(
        "✅ Giveawayを終了しました",
        ephemeral=True
    )

async def setup(bot):
await bot.add_cog(
Giveaway(bot)
)
