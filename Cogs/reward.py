import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from .reward_views import RewardPanelView


DATA_FILE = "reward_items.json"


# =====================
# DATA
# =====================
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
    return data


# =====================
# COG
# =====================
class Reward(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # LOG SETTING (NEW)
    # =====================
    @app_commands.command(name="reward_log_set", description="受け取りログの送信先を設定します")
    @app_commands.checks.has_permissions(administrator=True)
    async def reward_log_set(self, interaction: discord.Interaction, channel: discord.TextChannel):
        data = load_data()
        gid = str(interaction.guild.id)
        data = ensure_guild(data, gid)

        data[gid]["log_channel"] = channel.id
        save_data(data)

        await interaction.response.send_message(f"✅ ログ送信先を {channel.mention} に設定しました。", ephemeral=True)

    # =====================
    # ADD
    # =====================
    @app_commands.command(name="reward_add", description="商品追加")
    async def reward_add(self, interaction: discord.Interaction, name: str, infinite: bool = False):
        data = load_data()
        gid = str(interaction.guild.id)
        data = ensure_guild(data, gid)

        if name in data[gid]["items"]:
            return await interaction.response.send_message("❌ 既に存在", ephemeral=True)

        data[gid]["items"][name] = {
            "mode": "infinite" if infinite else "finite",
            "stock": []
        }

        save_data(data)
        await interaction.response.send_message(f"✅ 商品作成: {name}", ephemeral=True)

    # =====================
    # STOCK
    # =====================
    @app_commands.command(name="reward_stock", description="在庫追加")
    async def reward_stock(self, interaction: discord.Interaction, name: str, file: discord.Attachment):
        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data or name not in data[gid]["items"]:
            return await interaction.response.send_message("❌ 商品なし", ephemeral=True)

        raw = await file.read()
        text = raw.decode("utf-8", errors="ignore")

        if not text.strip():
            return await interaction.response.send_message("❌ ファイルが空です", ephemeral=True)

        data[gid]["items"][name]["stock"].append(text)
        save_data(data)

        await interaction.response.send_message(f"✅ 在庫を1件追加しました（全文保存）", ephemeral=True)

    # =====================
    # DELETE
    # =====================
    @app_commands.command(name="reward_delete", description="削除")
    async def reward_delete(self, interaction: discord.Interaction, name: str):
        data = load_data()
        gid = str(interaction.guild.id)

        if gid in data and name in data[gid]["items"]:
            del data[gid]["items"][name]
            save_data(data)

        await interaction.response.send_message("🗑 削除完了", ephemeral=True)

    # =====================
    # LIST
    # =====================
    @app_commands.command(name="reward_list", description="一覧")
    async def reward_list(self, interaction: discord.Interaction):
        data = load_data()
        gid = str(interaction.guild.id)

        items = data.get(gid, {}).get("items", {})

        if not items:
            return await interaction.response.send_message("❌ 商品が登録されていません。", ephemeral=True)

        embed = discord.Embed(title="📦 商品一覧", color=discord.Color.blurple())

        for name, item in items.items():
            stock_list = item.get("stock", [])
            mode = item.get("mode")
            stock_text = "∞" if mode == "infinite" else f"{len(stock_list)}件"
            embed.add_field(name=name, value=f"在庫: {stock_text}", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # =====================
    # PANEL
    # =====================
    @app_commands.command(name="reward_panel", description="パネル設置")
    async def reward_panel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        embed = discord.Embed(
            title="🎁 配布パネル",
            description="ボタンから商品を受け取れます",
            color=discord.Color.gold()
        )
        await channel.send(embed=embed, view=RewardPanelView())
        await interaction.response.send_message("✅ 設置完了", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Reward(bot))
    bot.add_view(RewardPanelView())
