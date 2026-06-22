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
# CONFIRM VIEW
# =====================
class ConfirmView(discord.ui.View):
    def __init__(self, item_name: str):
        super().__init__(timeout=60)

        self.item_name = item_name

    @discord.ui.button(
        label="✅ 受け取る",
        style=discord.ButtonStyle.success
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data:
            return await interaction.response.send_message(
                "❌ 商品が存在しません",
                ephemeral=True
            )

        if self.item_name not in data[gid]:
            return await interaction.response.send_message(
                "❌ 商品が存在しません",
                ephemeral=True
            )

        item = data[gid][self.item_name]

        mode = item.get("mode", "finite")
        stock = item.get("stock", [])

        if len(stock) == 0:
            return await interaction.response.send_message(
                "❌ 在庫切れです",
                ephemeral=True
            )

        # infinite
        if mode == "infinite":
            reward_text = stock[0]

        # finite
        else:
            reward_text = stock.pop(0)
            data[gid][self.item_name]["stock"] = stock
            save_data(data)

        try:

            embed = discord.Embed(
                title=f"📦 {self.item_name}",
                description=reward_text,
                color=discord.Color.green()
            )

            await interaction.user.send(
                embed=embed
            )

            await interaction.response.send_message(
                "✅ DMへ送信しました",
                ephemeral=True
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ DMが受け取れません",
                ephemeral=True
            )


# =====================
# SELECT
# =====================
class ItemSelect(discord.ui.Select):

    def __init__(self, guild_id: str):

        data = load_data()

        options = []

        if guild_id in data:

            for item_name, item_data in data[guild_id].items():

                mode = item_data.get("mode")

                if mode == "infinite":
                    stock_text = "∞"

                else:
                    stock_text = str(
                        len(
                            item_data.get("stock", [])
                        )
                    )

                options.append(
                    discord.SelectOption(
                        label=item_name[:100],
                        value=item_name,
                        description=f"在庫: {stock_text}"
                    )
                )

        super().__init__(
            placeholder="📦 商品を選択",
            min_values=1,
            max_values=1,
            options=options[:25]
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        item_name = self.values[0]

        data = load_data()
        gid = str(interaction.guild.id)

        item = data[gid][item_name]

        mode = item.get("mode")

        if mode == "infinite":
            stock_text = "∞"
        else:
            stock_text = str(
                len(item.get("stock", []))
            )

        embed = discord.Embed(
            title="📦 商品受け取り確認",
            description=(
                f"商品: **{item_name}**\n"
                f"在庫: **{stock_text}**\n\n"
                f"受け取りますか？"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed,
            view=ConfirmView(item_name),
            ephemeral=True
        )


class ItemSelectView(discord.ui.View):
    def __init__(self, guild_id: str):
        super().__init__(timeout=60)

        self.add_item(
            ItemSelect(guild_id)
        )
        # =====================
# PANEL VIEW
# =====================
class RewardPanelView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📦 商品を受け取る",
        style=discord.ButtonStyle.primary,
        custom_id="reward_open_panel"
    )
    async def open_panel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        data = load_data()

        gid = str(interaction.guild.id)

        if gid not in data:
            return await interaction.response.send_message(
                "❌ 商品がありません",
                ephemeral=True
            )

        if len(data[gid]) == 0:
            return await interaction.response.send_message(
                "❌ 商品がありません",
                ephemeral=True
            )

        await interaction.response.send_message(
            "📦 商品を選択してください",
            view=ItemSelectView(gid),
            ephemeral=True
        )

# =====================
# COG
# =====================
class RewardPanel(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="reward_panel",
        description="配布パネルを設置"
    )
    @app_commands.describe(
        channel="設置先チャンネル"
    )
    async def reward_panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        embed = discord.Embed(
            title="🎁 配布パネル",
            description=(
                "下のボタンから商品を受け取れます。"
            ),
            color=discord.Color.gold()
        )

        embed.add_field(
            name="📦 受け取り方法",
            value=(
                "ボタンを押す\n"
                "↓\n"
                "商品を選択\n"
                "↓\n"
                "DMで受け取る"
            ),
            inline=False
        )

        await channel.send(
            embed=embed,
            view=RewardPanelView()
        )

        await interaction.response.send_message(
            "✅ 配布パネルを設置しました",
            ephemeral=True
        )


# =====================
# SETUP
# =====================
async def setup(bot):

    await bot.add_cog(
        RewardPanel(bot)
    )
