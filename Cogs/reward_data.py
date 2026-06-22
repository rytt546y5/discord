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
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )


# =====================
# COG
# =====================
class RewardData(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # 商品作成
    # =====================
    @app_commands.command(
        name="reward_add",
        description="商品を作成"
    )
    @app_commands.describe(
        name="商品名",
        infinite="無限配布にするか"
    )
    async def reward_add(
        self,
        interaction: discord.Interaction,
        name: str,
        infinite: bool = False
    ):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data:
            data[gid] = {}

        if name in data[gid]:
            return await interaction.response.send_message(
                "❌ 既に存在します",
                ephemeral=True
            )

        data[gid][name] = {
            "mode": "infinite" if infinite else "finite",
            "stock": []
        }

        save_data(data)

        await interaction.response.send_message(
            f"✅ 商品作成: {name}",
            ephemeral=True
        )

    # =====================
    # 商品削除
    # =====================
    @app_commands.command(
        name="reward_delete",
        description="商品削除"
    )
    async def reward_delete(
        self,
        interaction: discord.Interaction,
        name: str
    ):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data:
            return await interaction.response.send_message(
                "❌ データなし",
                ephemeral=True
            )

        if name not in data[gid]:
            return await interaction.response.send_message(
                "❌ 商品なし",
                ephemeral=True
            )

        del data[gid][name]

        save_data(data)

        await interaction.response.send_message(
            f"🗑 商品削除: {name}",
            ephemeral=True
        )

    # =====================
    # 商品一覧
    # =====================
    @app_commands.command(
        name="reward_list",
        description="商品一覧"
    )
    async def reward_list(
        self,
        interaction: discord.Interaction
    ):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data or not data[gid]:
            return await interaction.response.send_message(
                "❌ 商品なし",
                ephemeral=True
            )

        embed = discord.Embed(
            title="📦 商品一覧",
            color=discord.Color.blurple()
        )

        for item_name, item_data in data[gid].items():

            stock_count = len(
                item_data.get("stock", [])
            )

            mode = item_data.get("mode")

            if mode == "infinite":
                stock_text = "∞"
            else:
                stock_text = str(stock_count)

            embed.add_field(
                name=item_name,
                value=f"在庫: {stock_text}",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # =====================
    # 在庫追加
    # =====================
    @app_commands.command(
        name="reward_stock",
        description="txtから在庫追加"
    )
    async def reward_stock(
        self,
        interaction: discord.Interaction,
        name: str,
        file: discord.Attachment
    ):

        if not file.filename.endswith(".txt"):
            return await interaction.response.send_message(
                "❌ txtのみ",
                ephemeral=True
            )

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data:
            return await interaction.response.send_message(
                "❌ 商品なし",
                ephemeral=True
            )

        if name not in data[gid]:
            return await interaction.response.send_message(
                "❌ 商品なし",
                ephemeral=True
            )

        raw = await file.read()

        text = raw.decode(
            "utf-8",
            errors="ignore"
        )

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        data[gid][name]["stock"].extend(lines)

        save_data(data)

        await interaction.response.send_message(
            f"✅ {len(lines)}件追加",
            ephemeral=True
        )

    # =====================
    # 在庫確認
    # =====================
    @app_commands.command(
        name="reward_stock_check",
        description="在庫確認"
    )
    async def reward_stock_check(
        self,
        interaction: discord.Interaction,
        name: str
    ):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data:
            return await interaction.response.send_message(
                "❌ 商品なし",
                ephemeral=True
            )

        if name not in data[gid]:
            return await interaction.response.send_message(
                "❌ 商品なし",
                ephemeral=True
            )

        item = data[gid][name]

        mode = item["mode"]

        if mode == "infinite":
            stock_text = "∞"
        else:
            stock_text = str(
                len(item["stock"])
            )

        await interaction.response.send_message(
            f"📦 {name}\n在庫: {stock_text}",
            ephemeral=True
        )

    # =====================
    # 在庫全削除
    # =====================
    @app_commands.command(
        name="reward_stock_clear",
        description="在庫削除"
    )
    async def reward_stock_clear(
        self,
        interaction: discord.Interaction,
        name: str
    ):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data:
            return await interaction.response.send_message(
                "❌ 商品なし",
                ephemeral=True
            )

        if name not in data[gid]:
            return await interaction.response.send_message(
                "❌ 商品なし",
                ephemeral=True
            )

        data[gid][name]["stock"] = []

        save_data(data)

        await interaction.response.send_message(
            f"🧹 {name} 在庫削除",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(
        RewardData(bot)
    )
