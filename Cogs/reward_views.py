import discord
import json
import os
import random

DATA_FILE = "reward_items.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class ConfirmView(discord.ui.View):
    def __init__(self, item_name):
        super().__init__(timeout=60)
        self.item_name = item_name

    @discord.ui.button(label="受け取る", style=discord.ButtonStyle.green)
    async def ok(self, interaction, button):

        data = load_data()
        gid = str(interaction.guild.id)

        item = data.get(gid, {}).get(self.item_name)

        if not item:
            return await interaction.response.send_message("なし", ephemeral=True)

        stock = item.get("stock", [])
        mode = item.get("mode")

        if not stock:
            return await interaction.response.send_message("在庫なし", ephemeral=True)

        reward = random.choice(stock) if mode == "infinite" else stock.pop(0)

        if mode != "infinite":
            data[gid][self.item_name]["stock"] = stock
            save_data(data)

        await interaction.user.send(f"📦 {self.item_name}\n{reward}")

        await interaction.response.send_message("DM送信完了", ephemeral=True)


class ItemSelect(discord.ui.Select):
    def __init__(self, gid):

        data = load_data().get(gid, {})

        options = []

        for name, item in data.items():

            stock = item.get("stock", [])
            mode = item.get("mode")

            options.append(
                discord.SelectOption(
                    label=name,
                    value=name,
                    description=f"{'∞' if mode=='infinite' else len(stock)}件"
                )
            )

        super().__init__(
            placeholder="商品選択",
            options=options[:25]
        )

    async def callback(self, interaction):

        name = self.values[0]
        gid = str(interaction.guild.id)

        await interaction.response.send_message(
            f"{name} を選択",
            view=ConfirmView(name),
            ephemeral=True
        )


class ItemView(discord.ui.View):
    def __init__(self, gid):
        super().__init__()
        self.add_item(ItemSelect(gid))


class RewardPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="受け取る",
        style=discord.ButtonStyle.primary,
        custom_id="reward_open"
    )
    async def open(self, interaction, button):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data:
            return await interaction.response.send_message("なし", ephemeral=True)

        await interaction.response.send_message(
            "選択してください",
            view=ItemView(gid),
            ephemeral=True
        )
