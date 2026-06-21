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
# CONFIRM VIEW
# =====================
class ConfirmView(discord.ui.View):
    def __init__(self, item: str):
        super().__init__(timeout=30)
        self.item = item

    @discord.ui.button(label="✅ 受け取る", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        try:
            embed = discord.Embed(
                title="📦 商品受け取り",
                description=f"**{self.item}** を受け取りました",
                color=discord.Color.green()
            )

            await interaction.user.send(embed=embed)

            await interaction.response.send_message(
                "📩 DMに送信しました",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ DMが無効です（受信設定を確認してください）",
                ephemeral=True
            )


# =====================
# SELECT MENU
# =====================
class ItemSelect(discord.ui.Select):
    def __init__(self, items: list[str]):

        clean_items = [i.strip() for i in items if i and i.strip()]

        options = [
            discord.SelectOption(
                label=i[:100],
                value=i[:100],
                description="選択して受け取る"
            )
            for i in clean_items[:25]
        ]

        super().__init__(
            placeholder="📦 商品を選択してください",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        selected = self.values[0]

        embed = discord.Embed(
            title="📦 確認",
            description=f"**{selected}** を受け取りますか？",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed,
            view=ConfirmView(selected),
            ephemeral=True
        )


class ItemSelectView(discord.ui.View):
    def __init__(self, items):
        super().__init__(timeout=None)
        self.add_item(ItemSelect(items))


# =====================
# MAIN PANEL VIEW
# =====================
class RewardPanelView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📦 商品を受け取る",
        style=discord.ButtonStyle.primary,
        custom_id="reward_open"
    )
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = load_data()
        gid = str(interaction.guild.id)

        items = data.get(gid, [])

        items = [i for i in items if i and i.strip()]

        if not items:
            return await interaction.response.send_message(
                "❌ 商品がありません",
                ephemeral=True
            )

        await interaction.response.send_message(
            "📦 商品を選択してください",
            view=ItemSelectView(items),
            ephemeral=True
        )


# =====================
# COG
# =====================
class RewardPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 商品追加（単体）
    @app_commands.command(
        name="reward_add",
        description="配布パネルに商品を追加"
    )
    @app_commands.describe(item="追加する商品名")
    async def add(self, interaction: discord.Interaction, item: str):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data:
            data[gid] = []

        # 重複防止
        if item not in data[gid]:
            data[gid].append(item)

        save_data(data)

        await interaction.response.send_message(
            f"✅ 商品追加: {item}",
            ephemeral=True
        )

    # パネル設置
    @app_commands.command(
        name="reward_panel",
        description="配布パネルを設置"
    )
    async def panel(self, interaction: discord.Interaction, channel: discord.TextChannel):

        embed = discord.Embed(
            title="🎁 配布パネル",
            description="ボタンを押して商品を受け取ってください",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="📌 使い方",
            value="ボタン → 商品選択 → 確認 → DM送信",
            inline=False
        )

        await channel.send(
            embed=embed,
            view=RewardPanelView()
        )

        await interaction.response.send_message(
            "✅ パネル設置完了",
            ephemeral=True
        )

    # 一括追加（txt）
    @app_commands.command(
        name="reward_stock",
        description="txt形式で商品を一括追加"
    )
    async def stock(self, interaction: discord.Interaction, text: str):

        items = [i.strip() for i in text.split("\n") if i.strip()]

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data:
            data[gid] = []

        for i in items:
            if i not in data[gid]:
                data[gid].append(i)

        save_data(data)

        await interaction.response.send_message(
            f"✅ {len(items)}件追加しました",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(RewardPanel(bot))
