import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "reward_items.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- UI Components ---

class ConfirmView(discord.ui.View):
    def __init__(self, item_name: str):
        super().__init__(timeout=60)
        self.item_name = item_name

    @discord.ui.button(label="受け取る", style=discord.ButtonStyle.green)
    async def ok(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        gid = str(interaction.guild.id)
        guild_data = data.get(gid, {"items": {}, "log_channel": None})
        item = guild_data.get("items", {}).get(self.item_name)

        if not item:
            return await interaction.response.send_message("❌ 商品が見つかりませんでした。", ephemeral=True)

        stock = item.get("stock", [])
        mode = item.get("mode", "finite")

        if not stock:
            return await interaction.response.send_message("❌ 在庫が切れています。", ephemeral=True)

        # 在庫処理
        reward_content = stock[0] if mode == "infinite" else stock.pop(0)
        if mode != "infinite":
            data[gid]["items"][self.item_name]["stock"] = stock
            save_data(data)

        # DM送信とログ
        dm_em = discord.Embed(title="📦 商品受け取り", description=reward_content, color=discord.Color.green())
        dm_em.add_field(name="商品名", value=self.item_name, inline=False)

        try:
            await interaction.user.send(embed=dm_em)
            await interaction.response.edit_message(content=f"✅ 「{self.item_name}」をDMへ送りました。", view=None)

            # === 指定されたログ形式 ===
            log_id = guild_data.get("log_channel")
            if log_id:
                chan = interaction.guild.get_channel(log_id)
                if chan:
                    log_em = discord.Embed(title="📥 受け取りログ", color=discord.Color.blue())
                    log_em.set_thumbnail(url=interaction.user.display_avatar.url) # アイコン
                    log_em.add_field(name="ユーザー", value=interaction.user.mention, inline=True) # メンション
                    log_em.add_field(name="商品名", value=self.item_name, inline=True) # 商品名
                    log_em.set_footer(text="ご利用ありがとうございます。") # 指定文字
                    await chan.send(embed=log_em)
        except discord.Forbidden:
            await interaction.response.send_message("❌ DM送信に失敗しました。", ephemeral=True)

class ItemSelect(discord.ui.Select):
    def __init__(self, gid: str):
        data = load_data().get(gid, {}).get("items", {})
        options = [discord.SelectOption(label=n[:100], description=f"在庫: {'∞' if i['mode']=='infinite' else len(i['stock'])}", value=n) for n, i in data.items()]
        if not options: options = [discord.SelectOption(label="商品なし", value="none")]
        super().__init__(placeholder="受け取る商品を選んでください", options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none": return
        await interaction.response.send_message(f"📦 **{self.values[0]}** を受け取りますか？", view=ConfirmView(self.values[0]), ephemeral=True)

class ItemView(discord.ui.View):
    def __init__(self, gid: str):
        super().__init__(timeout=60)
        self.add_item(ItemSelect(gid))

class RewardPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📦 商品を受け取る", style=discord.ButtonStyle.primary, custom_id="reward_open")
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        if not data.get(str(interaction.guild.id), {}).get("items"):
            return await interaction.response.send_message("❌ 商品がありません。", ephemeral=True)
        await interaction.response.send_message("商品を選択してください。", view=ItemView(str(interaction.guild.id)), ephemeral=True)

# --- Cog ---

class Reward(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(RewardPanelView())

    @app_commands.command(name="reward_log_set", description="ログ送信先を設定します")
    async def log_set(self, interaction: discord.Interaction, channel: discord.TextChannel):
        data = load_data()
        gid = str(interaction.guild.id)
        if gid not in data: data[gid] = {"items": {}, "log_channel": None}
        data[gid]["log_channel"] = channel.id
        save_data(data)
        await interaction.response.send_message(f"✅ ログ先を {channel.mention} に設定しました。", ephemeral=True)

    @app_commands.command(name="reward_panel", description="パネル設置")
    async def panel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await channel.send(embed=discord.Embed(title="📦 商品受取パネル", color=discord.Color.blue()), view=RewardPanelView())
        await interaction.response.send_message("✅ 設置完了", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Reward(bot))
