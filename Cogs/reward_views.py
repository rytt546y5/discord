import discord
import json
import os

REWARD_ITEMS_FILE = "reward_items.json"
REWARD_CONFIG_FILE = "reward_config.json" # ログ設定用

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

class ConfirmView(discord.ui.View):
    def __init__(self, item_name: str, guild_id: int):
        super().__init__(timeout=60)
        self.item_name = item_name
        self.guild_id = str(guild_id)

    @discord.ui.button(label="受け取る", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = load_json(REWARD_ITEMS_FILE)
        config = load_json(REWARD_CONFIG_FILE)
        
        guild_items = items.get(self.guild_id, {})
        item_data = guild_items.get(self.item_name)

        if not item_data or not item_data.get("stock"):
            return await interaction.response.send_message("❌ 在庫がありません。", ephemeral=True)

        # 在庫取得ロジック (pop(0) または [0])
        stock_list = item_data["stock"]
        if item_data["mode"] == "finite":
            reward_content = stock_list.pop(0)
        else:
            reward_content = stock_list[0]

        save_json(REWARD_ITEMS_FILE, items)

        # DM送信 (Embed)
        dm_embed = discord.Embed(
            title="📦 商品受け取り",
            description=reward_content,
            color=discord.Color.green()
        )
        dm_embed.add_field(name="商品名", value=self.item_name)

        try:
            await interaction.user.send(embed=dm_embed)
            await interaction.response.edit_message(content=f"✅ 「{self.item_name}」をDMへ送信しました。", view=None)
        except discord.Forbidden:
            return await interaction.response.send_message("❌ DMを送信できませんでした。設定を確認してください。", ephemeral=True)

        # ログ送信
        log_channel_id = config.get(self.guild_id, {}).get("log_channel")
        if log_channel_id:
            channel = interaction.guild.get_channel(int(log_channel_id))
            if channel:
                log_embed = discord.Embed(
                    title="📥 商品受け取りログ",
                    color=discord.Color.blue()
                )
                log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                log_embed.add_field(name="ユーザー", value=interaction.user.mention)
                log_embed.add_field(name="商品名", value=self.item_name)
                log_embed.set_footer(text="Reward System")
                await channel.send(embed=log_embed)

class ItemSelect(discord.ui.Select):
    def __init__(self, guild_id: int):
        items = load_json(REWARD_ITEMS_FILE)
        guild_items = items.get(str(guild_id), {})
        
        options = []
        for name, data in guild_items.items():
            count = len(data["stock"])
            if data["mode"] == "infinite" or count > 0:
                label = name[:100]
                desc = "在庫: ∞" if data["mode"] == "infinite" else f"在庫: {count}件"
                options.append(discord.SelectOption(label=label, description=desc, value=name))

        if not options:
            options.append(discord.SelectOption(label="在庫なし", value="none", disabled=True))

        super().__init__(placeholder="商品を選択してください", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none": return
        view = ConfirmView(self.values[0], interaction.guild.id)
        await interaction.response.send_message(f"📦 「{self.values[0]}」を受け取りますか？", view=view, ephemeral=True)

class ItemView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=60)
        self.add_item(ItemSelect(guild_id))

class RewardPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # 永続化

    @discord.ui.button(label="📦 商品を受け取る", style=discord.ButtonStyle.primary, custom_id="reward_panel_open")
    async def open_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("商品を選択してください。", view=ItemView(interaction.guild.id), ephemeral=True)
