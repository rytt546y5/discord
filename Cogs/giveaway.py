import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random


DATA_FILE = "giveaway.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# =====================
# VIEW
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
                "⚠ すでに参加済みです",
                ephemeral=True
            )

        data[gid].append(interaction.user.id)
        save_data(data)

        await interaction.response.send_message(
            "✅ 参加しました！",
            ephemeral=True
        )


# =====================
# COG
# =====================
class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="giveaway_panel",
        description="抽選イベントパネル設置"
    )
    @app_commands.describe(
        channel="設置チャンネル",
        title="タイトル",
        description="説明",
        image="画像（任意・添付）"
    )
    async def giveaway_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        description: str,
        image: discord.Attachment = None
    ):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.gold()
        )

        if image:
            embed.set_image(url=image.url)

        embed.add_field(
            name="🎉 参加方法",
            value="ボタンを押すだけで参加できます",
            inline=False
        )

        msg = await channel.send(
            embed=embed,
            view=GiveawayView()
        )

        await interaction.response.send_message(
            f"✅ giveaway設置完了: {msg.jump_url}",
            ephemeral=True
        )

    # =====================
    # 抽選コマンド
    # =====================
    @app_commands.command(
        name="giveaway_pick",
        description="当選者をランダム選出"
    )
    async def pick(self, interaction: discord.Interaction):

        data = load_data()
        gid = str(interaction.channel.last_message_id)

        users = data.get(gid, [])

        if not users:
            return await interaction.response.send_message(
                "❌ 参加者なし",
                ephemeral=True
            )

        winner_id = random.choice(users)

        await interaction.response.send_message(
            f"🎉 当選者: <@{winner_id}>"
        )


async def setup(bot):
    await bot.add_cog(Giveaway(bot))
