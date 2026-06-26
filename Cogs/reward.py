import discord
from discord.ext import commands
from discord import app_commands
import json
import os

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
        data[gid] = {}
    return data


# =====================
# COG
# =====================
class Reward(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # 商品追加
    # =====================
    @app_commands.command(name="reward_add", description="商品追加")
    async def reward_add(self, interaction: discord.Interaction, name: str, infinite: bool = False):

        data = load_data()
        gid = str(interaction.guild.id)

        data = ensure_guild(data, gid)

        if name in data[gid]:
            return await interaction.response.send_message("❌ 既に存在", ephemeral=True)

        data[gid][name] = {
            "mode": "infinite" if infinite else "finite",
            "stock": []
        }

        save_data(data)

        await interaction.response.send_message(f"✅ 商品作成: {name}", ephemeral=True)

    # =====================
    # 在庫追加（txt）
    # =====================
    @app_commands.command(name="reward_stock", description="在庫追加")
    async def reward_stock(self, interaction: discord.Interaction, name: str, file: discord.Attachment):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data or name not in data[gid]:
            return await interaction.response.send_message("❌ 商品なし", ephemeral=True)

        raw = await file.read()
        text = raw.decode("utf-8", errors="ignore")

        items = [x.strip() for x in text.splitlines() if x.strip()]

        data[gid][name]["stock"].extend(items)
        save_data(data)

        await interaction.response.send_message(f"✅ {len(items)}件追加", ephemeral=True)

    # =====================
    # 商品削除
    # =====================
    @app_commands.command(name="reward_delete", description="商品削除")
    async def reward_delete(self, interaction: discord.Interaction, name: str):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid in data and name in data[gid]:
            del data[gid][name]
            save_data(data)

        await interaction.response.send_message("🗑 削除完了", ephemeral=True)

    # =====================
    # 一覧
    # =====================
    @app_commands.command(name="reward_list", description="商品一覧")
    async def reward_list(self, interaction: discord.Interaction):

        data = load_data()
        gid = str(interaction.guild.id)

        items = data.get(gid, {})

        if not items:
            return await interaction.response.send_message("❌ 商品なし", ephemeral=True)

        embed = discord.Embed(
            title="📦 商品一覧",
            color=discord.Color.blurple()
        )

        for name, item in items.items():
            stock = item.get("stock", [])
            mode = item.get("mode")

            stock_text = "∞" if mode == "infinite" else str(len(stock))

            embed.add_field(
                name=name,
                value=f"在庫: {stock_text}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # =====================
    # パネル設置
    # =====================
    @app_commands.command(name="reward_panel", description="配布パネル設置")
    async def reward_panel(self, interaction: discord.Interaction, channel: discord.TextChannel):

        embed = discord.Embed(
            title="🎁 配布パネル",
            description="下のボタンから商品を受け取れます",
            color=discord.Color.gold()
        )

        view = RewardPanelView()

        await channel.send(embed=embed, view=view)

        await interaction.response.send_message("✅ パネル設置完了", ephemeral=True)


# =====================
# 永続View登録
# =====================
async def setup(bot):

    from reward_views import RewardPanelView

    # 永続View登録（重要）
    bot.add_view(RewardPanelView())

    await bot.add_cog(Reward(bot))
