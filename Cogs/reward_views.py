import discord
import json
import os
import random

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
    def __init__(self, item_name: str):
        super().__init__(timeout=60)
        self.item_name = item_name

    @discord.ui.button(
        label="✅ 受け取る",
        style=discord.ButtonStyle.success
    )
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = load_data()
        gid = str(interaction.guild.id)

        item = data.get(gid, {}).get(self.item_name)

        if not item:
            return await interaction.response.send_message("❌ 商品なし", ephemeral=True)

        stock = item.get("stock", [])
        mode = item.get("mode", "finite")

        if not stock:
            return await interaction.response.send_message("❌ 在庫なし", ephemeral=True)

        # =====================
        # reward logic
        # =====================
        if mode == "infinite":
            reward = random.choice(stock)  # 無限はランダム
        else:
            reward = stock.pop(0)
            data[gid][self.item_name]["stock"] = stock
            save_data(data)

        try:
            embed = discord.Embed(
                title=f"📦 {self.item_name}",
                description=reward,
                color=discord.Color.green()
            )

            await interaction.user.send(embed=embed)

            await interaction.response.send_message(
                "✅ DM送信完了",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ DM受信不可",
                ephemeral=True
            )


# =====================
# SELECT MENU
# =====================
class ItemSelect(discord.ui.Select):
    def __init__(self, guild_id: str):

        data = load_data()
        guild_data = data.get(guild_id, {})

        options = []

        for name, item in guild_data.items():

            stock = item.get("stock", [])
            mode = item.get("mode")

            stock_text = "∞" if mode == "infinite" else str(len(stock))

            options.append(
                discord.SelectOption(
                    label=name[:100],
                    value=name,
                    description=f"在庫: {stock_text}"
                )
            )

        super().__init__(
            placeholder="📦 商品を選択",
            min_values=1,
            max_values=1,
            options=options[:25]
        )

    async def callback(self, interaction: discord.Interaction):

        name = self.values[0]
        data = load_data()
        gid = str(interaction.guild.id)

        item = data.get(gid, {}).get(name)

        if not item:
            return await interaction.response.send_message("❌ 商品なし", ephemeral=True)

        stock = item.get("stock", [])
        mode = item.get("mode")

        stock_text = "∞" if mode == "infinite" else str(len(stock))

        embed = discord.Embed(
            title="📦 確認",
            description=f"{name}\n在庫: {stock_text}\n\n受け取りますか？",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed,
            view=ConfirmView(name),
            ephemeral=True
        )


# =====================
# SELECT VIEW
# =====================
class ItemSelectView(discord.ui.View):
    def __init__(self, guild_id: str):
        super().__init__(timeout=60)
        self.add_item(ItemSelect(guild_id))


# =====================
# PANEL VIEW (PERSISTENT)
# =====================
class RewardPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📦 商品を受け取る",
        style=discord.ButtonStyle.primary,
        custom_id="reward_open_panel"
    )
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data or not data[gid]:
            return await interaction.response.send_message("❌ 商品なし", ephemeral=True)

        await interaction.response.send_message(
            "📦 商品一覧",
            view=ItemSelectView(gid),
            ephemeral=True
        )
