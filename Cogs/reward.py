import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from .reward_views import RewardPanelView

DATA_FILE = "reward_items.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def ensure_guild(data, gid):
    if gid not in data:
        data[gid] = {"items": {}, "log_channel": None}
    if "items" not in data[gid]:
        data[gid] = {"items": {}, "log_channel": None}
    return data

class Reward(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reward_log_set", description="受け取りログの送信先を設定します")
    @app_commands.checks.has_permissions(administrator=True)
    async def reward_log_set(self, interaction: discord.Interaction, channel: discord.TextChannel):
        data = load_data()
        gid = str(interaction.guild.id)
        data = ensure_guild(data, gid)
        data[gid]["log_channel"] = channel.id
        save_data(data)
        await interaction.response.send_message(f"✅ ログ送信先を {channel.mention} に設定しました。", ephemeral=True)

    @app_commands.command(name="reward_add", description="新規商品の作成")
    async def reward_add(self, interaction: discord.Interaction, name: str, infinite: bool = False):
        data = load_data()
        gid = str(interaction.guild.id)
        data = ensure_guild(data, gid)
        if name in data[gid]["items"]:
            return await interaction.response.send_message("❌ 同名の商品が既に存在します。", ephemeral=True)
        data[gid]["items"][name] = {"mode": "infinite" if infinite else "finite", "stock": []}
        save_data(data)
        await interaction.response.send_message(f"✅ 商品「{name}」を作成しました。", ephemeral=True)

    @app_commands.command(name="reward_stock", description="在庫追加（txtの内容全文を1件として保存）")
    async def reward_stock(self, interaction: discord.Interaction, name: str, file: discord.Attachment):
        data = load_data()
        gid = str(interaction.guild.id)
        data = ensure_guild(data, gid)
        if name not in data[gid]["items"]:
            return await interaction.response.send_message("❌ 商品が見つかりません。", ephemeral=True)
        raw = await file.read()
        text = raw.decode("utf-8", errors="ignore")
        if not text.strip():
            return await interaction.response.send_message("❌ ファイルが空です。", ephemeral=True)
        data[gid]["items"][name]["stock"].append(text)
        save_data(data)
        await interaction.response.send_message(f"✅ 「{name}」に在庫を追加しました。", ephemeral=True)

    @app_commands.command(name="reward_delete", description="商品の削除")
    async def reward_delete(self, interaction: discord.Interaction, name: str):
        data = load_data()
        gid = str(interaction.guild.id)
        if gid in data and name in data[gid]["items"]:
            del data[gid]["items"][name]
            save_data(data)
            await interaction.response.send_message(f"🗑 商品「{name}」を削除しました。", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 商品が見つかりません。", ephemeral=True)

    @app_commands.command(name="reward_list", description="在庫状況一覧")
    async def reward_list(self, interaction: discord.Interaction):
        data = load_data()
        gid = str(interaction.guild.id)
        items = data.get(gid, {}).get("items", {})
        if not items:
            return await interaction.response.send_message("❌ 登録されている商品はありません。", ephemeral=True)
        embed = discord.Embed(title="📦 在庫一覧", color=discord.Color.blurple())
        for name, item in items.items():
            stock_list = item.get("stock", [])
            mode = item.get("mode")
            stock_text = "∞" if mode == "infinite" else f"{len(stock_list)}件"
            embed.add_field(name=name, value=f"在庫: {stock_text}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="reward_panel", description="配布パネルを設置")
    async def reward_panel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        embed = discord.Embed(
            title="🎁 商品配布パネル",
            description="下のボタンから商品を選択して受け取ってください。",
            color=discord.Color.gold()
        )
        await channel.send(embed=embed, view=RewardPanelView())
        await interaction.response.send_message("✅ パネルを設置しました。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Reward(bot))
    bot.add_view(RewardPanelView())
