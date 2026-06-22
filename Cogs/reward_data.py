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


# =====================
# COG
# =====================
class RewardData(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # 追加（管理用）
    # =====================
    @app_commands.command(
        name="reward_admin_add",
        description="商品を追加（管理用）"
    )
    async def add(self, interaction: discord.Interaction, name: str, mode: str = "finite"):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data:
            data[gid] = {}

        if name not in data[gid]:
            data[gid][name] = {
                "mode": mode,
                "stock": []
            }

        save_data(data)

        await interaction.response.send_message(
            f"✅ 追加: {name}",
            ephemeral=True
        )

    # =====================
    # 在庫追加
    # =====================
    @app_commands.command(
        name="reward_admin_stock",
        description="在庫を追加（管理用）"
    )
    async def stock(self, interaction: discord.Interaction, name: str, text: str):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data or name not in data[gid]:
            return await interaction.response.send_message(
                "❌ 商品が存在しません",
                ephemeral=True
            )

        items = [i.strip() for i in text.split("\n") if i.strip()]

        data[gid][name]["stock"].extend(items)

        save_data(data)

        await interaction.response.send_message(
            f"✅ {len(items)}件追加しました",
            ephemeral=True
        )

    # =====================
    # 削除
    # =====================
    @app_commands.command(
        name="reward_admin_delete",
        description="商品削除（管理用）"
    )
    async def delete(self, interaction: discord.Interaction, name: str):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid in data and name in data[gid]:
            del data[gid][name]
            save_data(data)

        await interaction.response.send_message(
            f"🗑 削除: {name}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(RewardData(bot))
