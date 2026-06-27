import discord
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
    def __init__(self, item_name: str):
        super().__init__(timeout=60)
        self.item_name = item_name

    @discord.ui.button(label="受け取る", style=discord.ButtonStyle.green)
    async def ok(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = load_data()
        gid = str(interaction.guild.id)

        item = data.get(gid, {}).get(self.item_name)

        if not item:
            return await interaction.response.send_message("❌ 商品が見つかりません。", ephemeral=True)

        stock = item.get("stock", [])
        mode = item.get("mode", "finite")

        if not stock:
            return await interaction.response.send_message("❌ 在庫がありません。", ephemeral=True)

        # =====================
        # 受け取りロジック (修正仕様)
        # =====================
        if mode == "infinite":
            # 無限：先頭を参照（削除しない）
            reward_content = stock[0]
        else:
            # 有限：先頭を削除して取得
            reward_content = stock.pop(0)
            data[gid][self.item_name]["stock"] = stock
            save_data(data)

        # =====================
        # DM送信 (Embed化)
        # =====================
        embed = discord.Embed(
            title="📦 商品受け取り",
            description=reward_content,
            color=discord.Color.green()
        )
        embed.add_field(name="商品名", value=self.item_name, inline=False)

        try:
            await interaction.user.send(embed=embed)

            await interaction.response.send_message(
                f"✅ 「{self.item_name}」をDMに送信しました。",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ DMを送信できませんでした。サーバー設定で「ダイレクトメッセージ」を許可してください。",
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

            # 在庫表示の切り替え
            stock_label = "∞" if mode == "infinite" else f"{len(stock)}件"

            options.append(
                discord.SelectOption(
                    label=name[:100],
                    value=name,
                    description=f"在庫: {stock_label}"
                )
            )

        # 商品が空の場合のプレースホルダー
        if not options:
            options.append(discord.SelectOption(label="商品がありません", value="none"))

        super().__init__(
            placeholder="📦 商品を選択してください",
            min_values=1,
            max_values=1,
            options=options[:25]
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            return

        name = self.values[0]
        await interaction.response.send_message(
            f"📦 **{name}** を受け取りますか？",
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
        label="📦 商品を受け取る",
        style=discord.ButtonStyle.primary,
        custom_id="reward_open"
    )
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = load_data()
        gid = str(interaction.guild.id)

        if gid not in data or not data[gid]:
            return await interaction.response.send_message(
                "❌ 現在、提供可能な商品がありません。",
                ephemeral=True
            )

        await interaction.response.send_message(
            "表示されたメニューから商品を選択してください。",
            view=ItemView(gid),
            ephemeral=True
        )
