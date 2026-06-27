import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import random
import time
from datetime import datetime, timedelta

# 抽選データ保存用
DATA_FILE = "giveaway_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

class GiveawayView(discord.ui.View):
    def __init__(self, message_id: int):
        super().__init__(timeout=None)
        self.message_id = message_id

    @discord.ui.button(
        label="🎉 参加する",
        style=discord.ButtonStyle.green,
        custom_id="giveaway_join"
    )
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        gid = str(self.message_id)

        if gid not in data:
            return await interaction.response.send_message("❌ この抽選データは見つかりません。", ephemeral=True)
        
        if data[gid].get("ended", False):
            return await interaction.response.send_message("⚠ この抽選は既に終了しています。", ephemeral=True)

        if interaction.user.id in data[gid]["users"]:
            return await interaction.response.send_message("⚠ すでに参加済みです", ephemeral=True)

        data[gid]["users"].append(interaction.user.id)
        save_data(data)

        await interaction.response.send_message("✅ 参加を受け付けました！", ephemeral=True)

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    @tasks.loop(seconds=60)
    async def check_giveaways(self):
        data = load_data()
        now = time.time()
        changed = False

        for msg_id, info in list(data.items()):
            if not info.get("ended", False) and info.get("end_time", 0) <= now:
                await self.end_giveaway(msg_id, info)
                info["ended"] = True
                changed = True

        if changed:
            save_data(data)

    async def end_giveaway(self, msg_id, info):
        channel = self.bot.get_channel(info["channel_id"])
        if not channel:
            return

        users = info.get("users", [])
        title = info.get("title", "抽選")
        
        if not users:
            await channel.send(f"📢 **{title}** の抽選結果\n参加者がいなかったため、当選者はありませんでした。")
            return

        winner_id = random.choice(users)
        
        embed = discord.Embed(
            title="🎊 抽選結果発表 🎊",
            description=f"**{title}** の当選者が決定しました！",
            color=discord.Color.purple()
        )
        embed.add_field(name="当選者", value=f"<@{winner_id}>") # ここを修正しました
        embed.set_footer(text="おめでとうございます！")
        
        await channel.send(content=f"Congratulations <@{winner_id}>!", embed=embed)

    @app_commands.command(name="giveaway_panel", description="抽選イベントパネルを設置します")
    @app_commands.describe(
        channel="パネルを設置するチャンネル",
        title="抽選のタイトル",
        description="抽選の説明文",
        minutes="締切までの時間（分単位）",
        image="パネルに表示する画像 (任意)"
    )
    async def giveaway_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        description: str,
        minutes: int,
        image: discord.Attachment = None
    ):
        end_timestamp = int(time.time() + (minutes * 60))
        time_display = f"<t:{end_timestamp}:F> (<t:{end_timestamp}:R>)"

        embed = discord.Embed(
            title=f"🎉 GIVEAWAY: {title}",
            description=f"{description}\n\n**締切:** {time_display}",
            color=discord.Color.gold()
        )
        embed.add_field(name="🎉 参加方法", value="下のボタンを押して参加！", inline=False)
        if image:
            embed.set_image(url=image.url)

        msg = await channel.send(embed=embed)
        view = GiveawayView(msg.id)
        await msg.edit(view=view)

        data = load_data()
        data[str(msg.id)] = {
            "guild_id": interaction.guild.id,
            "channel_id": channel.id,
            "title": title,
            "users": [],
            "end_time": end_timestamp,
            "ended": False
        }
        save_data(data)

        await interaction.response.send_message(f"✅ Giveawayを開始しました（締切: {minutes}分後）", ephemeral=True)

    @app_commands.command(name="giveaway_pick", description="手動で今すぐ当選者を選びます")
    async def pick(self, interaction: discord.Interaction, message_id: str):
        data = load_data()
        info = data.get(message_id)

        if not info:
            return await interaction.response.send_message("❌ 抽選データが見つかりません。", ephemeral=True)

        if info.get("ended"):
            return await interaction.response.send_message("❌ この抽選は既に終了しています。", ephemeral=True)

        await self.end_giveaway(message_id, info)
        info["ended"] = True
        save_data(data)
        await interaction.response.send_message("✅ 強制的に抽選を行いました。", ephemeral=True)

async def setup(bot):
    data = load_data()
    for msg_id in data.keys():
        if msg_id.isdigit():
            bot.add_view(GiveawayView(int(msg_id)))

    await bot.add_cog(Giveaway(bot))
