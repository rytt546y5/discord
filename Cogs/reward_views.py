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

    @discord.ui.button(label="受け取る", style=discord.ButtonStyle.green)
    async def ok(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = load_data()
        gid = str(interaction.guild.id)

        item = data.get(gid, {}).get(self.item_name)

        if not item:
            return await interaction.response.send_message("❌ 商品なし", ephemeral=True)

        stock = item.get("stock", [])
        mode = item.get("mode", "finite")

        if not stock:
            return await interaction.response.send_message("❌ 在庫なし", ephemeral=True)

        # reward logic
        reward = random.choice(stock) if mode == "infinite" else stock.pop(0)

        if mode != "infinite":
            data[gid][self.item_name]["stock"] = stock
            save_data(data)

        try:
            await interaction.user.send(
                f"📦 {self.item_name}\n{reward}"
            )

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
    def __init__(self, gid: str):

        data = load_data().get(gid, {})

        options = []

        for name, item in data.items():

            stock = item.get("stock", [])
            mode = item.get("mode", "finite")

            options.append(
                discord.SelectOption(
                    label=name[:100],
                    value=name,
                    description=f"{'∞' if mode=='infinite' else len(stock)}件"
                )
            )

        super().__init__(
            placeholder="📦 商品を選択してください",
            min_values=1,
            max_values=1,
            options=options[:25]
        )

    async def callback(self, interaction: discord.Interaction):

        name = self.values[0]
        gid = str(interaction.guild.id)

        await interaction.response.send_message(
            f"📦 {name} を選択しました",
            view=ConfirmView(name),
            ephemeral=True
        )


# =====================
# VIEW WRAPPER
# =====================
class ItemView(discord.ui.View):
    def __init__(self, gid: str):
        super().__init__(timeout=60)
        self.add_item(ItemSelect(gid))


# =====================
# PANEL VIEW (PERSISTENT)
# =====================
class RewardPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📦 受け取る",
        style=discord.ButtonStyle.primary,
        custom_id="reward_open"
    )
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data or not data[gid]:
            return await interaction.response.send_message(
                "❌ 商品なし",
                ephemeral=True
            )

        await interaction.response.send_message(
            "📦 商品一覧",
            view=ItemView(gid),
            ephemeral=True
        )
