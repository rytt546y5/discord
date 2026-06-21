import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import json
import os

DATA_FILE = "giveaway_data.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# =====================
# GIVEAWAY VIEW
# =====================
class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎉 参加する",
        style=discord.ButtonStyle.green,
        custom_id="giveaway_join"
    )
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()

        gid = str(interaction.message.id)

        if gid not in data:
            data[gid] = []

        if interaction.user.id in data[gid]:
            return await interaction.response.send_message(
                "❌ すでに参加済み",
                ephemeral=True
            )

        data[gid].append(interaction.user.id)
        save_data(data)

        await interaction.response.send_message(
            "✅ 参加しました",
            ephemeral=True
        )


# =====================
# COG
# =====================
class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="giveaway",
        description="抽選イベント作成"
    )
    @app_commands.default_permissions(administrator=True)
    async def giveaway(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        prize: str,
        winners: int,
        duration: int
    ):
        embed = discord.Embed(
            title="🎉 GIVEAWAY",
            description=f"**景品:** {prize}\n**当選人数:** {winners}\n**時間:** {duration}秒",
            color=discord.Color.gold()
        )

        msg = await channel.send(embed=embed, view=GiveawayView())

        await interaction.response.send_message(
            "✅ Giveaway作成完了",
            ephemeral=True
        )

        await asyncio.sleep(duration)

        data = load_data()
        participants = data.get(str(msg.id), [])

        if not participants:
            await channel.send("❌ 参加者なし")
            return

        winners_list = random.sample(
            participants,
            k=min(winners, len(participants))
        )

        mentions = []
        for user_id in winners_list:
            mentions.append(f"<@{user_id}>")

        await channel.send(
            f"🏆 当選者: {' '.join(mentions)}"
        )


# =====================
# SETUP
# =====================
async def setup(bot):
    await bot.add_cog(Giveaway(bot))
