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
        
        # 構造の安全な取得
        guild_data = data.get(gid, {"items": {}, "log_channel": None})
        items = guild_data.get("items", {})
        item = items.get(self.item_name)

        if not item:
            return await interaction.response.send_message("❌ 商品が見つかりません。", ephemeral=True)

        stock = item.get("stock", [])
        mode = item.get("mode", "finite")

        if not stock:
            return await interaction.response.send_message("❌ 在庫がありません。", ephemeral=True)

        # 受け取りロジック (有限: pop(0) / 無限: stock[0])
        if mode == "infinite":
            reward_content = stock[0]
        else:
            reward_content = stock.pop(0)
            data[gid]["items"][self.item_name]["stock"] = stock
            save_data(data)

        # ユーザーへのDM送信 (Embed形式)
        dm_embed = discord.Embed(
            title="📦 商品受け取り",
            description=reward_content,
            color=discord.Color.green()
        )
        dm_embed.add_field(name="商品名", value=self.item_name, inline=False)

        try:
            await interaction.user.send(embed=dm_embed)
            await interaction.response.edit_message(content=f"✅ 「{self.item_name}」をDMに送信しました。", view=None)

            # =====================
            # 管理者ログ送信
            # =====================
            log_channel_id = guild_data.get("log_channel")
            if log_channel_id:
                log_channel = interaction.guild.get_channel(log_channel_id)
                if log_channel:
                    log_embed = discord.Embed(
                        title="📥 商品受け取りログ",
                        color=discord.Color.blue()
                    )
                    log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                    log_embed.add_field(name="ユーザー", value=f"{interaction.user.mention} ({interaction.user.id})", inline=False)
                    log_embed.add_field(name="商品名", value=self.item_name, inline=False)
                    log_embed.add_field(name="メッセージ", value="ご利用ありがとうございます。", inline=False)
                    
                    await log_channel.send(embed=log_embed)

        except discord.Forbidden:
            await interaction.response.send_message("❌ DMを送信できません。サーバー設定でDMを許可してください。", ephemeral=True)

# =====================
# SELECT MENU
# =====================
class ItemSelect(discord.ui.Select):
    def __init__(self, gid: str):
        data = load_data()
        # 商品リストを取得
        items = data.get(gid, {}).get("items", {})
        
        options = []
        for name, item in items.items():
            stock = item.get("stock", [])
            mode = item.get("mode", "finite")
            stock_label = "∞" if mode == "infinite" else f"{len(stock)}件"
            
            # 在庫が0件でも選択肢には出す（ConfirmViewで弾く）
            options.append(discord.SelectOption(
                label=name[:100], 
                value=name, 
                description=f"在庫: {stock_label}"
            ))

        if not options:
            options.append(discord.SelectOption(label="商品がありません", value="none"))

        super().__init__(placeholder="📦 商品を選択してください", min_values=1, max_values=1, options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            return
        
        name = self.values[0]
        # 選択後に確認ボタンを出す
        await interaction.response.send_message(
            f"📦 **{name}** を受け取りますか？", 
            view=ConfirmView(name), 
            ephemeral=True
        )

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

    @discord.ui.button(label="📦 商品を受け取る", style=discord.ButtonStyle.primary, custom_id="reward_open")
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        gid = str(interaction.guild.id)
        
        # 商品があるかチェック
        items = data.get(gid, {}).get("items", {})
        if not items:
            return await interaction.response.send_message("❌ 現在、登録されている商品がありません。", ephemeral=True)

        # 商品選択メニューを表示
        await interaction.response.send_message("受け取りたい商品を選択してください。", view=ItemView(gid), ephemeral=True)
