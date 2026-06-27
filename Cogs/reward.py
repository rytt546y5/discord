import discord
from discord import app_commands
from discord.ext import commands
from Cogs.reward_views import RewardPanelView, load_json, save_json, REWARD_ITEMS_FILE, REWARD_CONFIG_FILE

class Reward(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reward_add", description="商品を追加します")
    @app_commands.describe(mode="finite(有限) か infinite(無限)")
    @app_commands.choices(mode=[
        app_commands.Choice(name="有限", value="finite"),
        app_commands.Choice(name="無限", value="infinite")
    ])
    async def reward_add(self, interaction: discord.Interaction, name: str, mode: str):
        items = load_json(REWARD_ITEMS_FILE)
        gid = str(interaction.guild.id)
        if gid not in items: items[gid] = {}
        items[gid][name] = {"mode": mode, "stock": []}
        save_json(REWARD_ITEMS_FILE, items)
        await interaction.response.send_message(f"✅ 商品「{name}」を{mode}モードで作成しました。", ephemeral=True)

    @app_commands.command(name="reward_stock", description="在庫を追加します（ファイル全文を1件として保存）")
    async def reward_stock(self, interaction: discord.Interaction, name: str, file: discord.Attachment):
        items = load_json(REWARD_ITEMS_FILE)
        gid = str(interaction.guild.id)
        if name not in items.get(gid, {}):
            return await interaction.response.send_message("❌ 商品が見つかりません。", ephemeral=True)
        content = (await file.read()).decode("utf-8") # 全文保持
        items[gid][name]["stock"].append(content)
        save_json(REWARD_ITEMS_FILE, items)
        await interaction.response.send_message(f"✅ 「{name}」に在庫を追加しました（在庫数: {len(items[gid][name]['stock'])}）", ephemeral=True)

    @app_commands.command(name="reward_delete", description="商品を削除します")
    async def reward_delete(self, interaction: discord.Interaction, name: str):
        items = load_json(REWARD_ITEMS_FILE)
        gid = str(interaction.guild.id)
        if name in items.get(gid, {}):
            del items[gid][name]
            save_json(REWARD_ITEMS_FILE, items)
            await interaction.response.send_message(f"✅ 商品「{name}」を削除しました。", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 商品が見つかりません。", ephemeral=True)

    @app_commands.command(name="reward_list", description="商品リストを表示します")
    async def reward_list(self, interaction: discord.Interaction):
        items = load_json(REWARD_ITEMS_FILE)
        gid = str(interaction.guild.id)
        guild_items = items.get(gid, {})
        if not guild_items:
            return await interaction.response.send_message("登録されている商品はありません。", ephemeral=True)
        embed = discord.Embed(title="📋 商品リスト", color=discord.Color.blue())
        for name, data in guild_items.items():
            stock_text = "在庫: ∞" if data["mode"] == "infinite" else f"在庫: {len(data['stock'])}件"
            embed.add_field(name=name, value=f"モード: {data['mode']}\n{stock_text}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="reward_panel", description="受取パネルを設置します")
    @app_commands.describe(
        title="パネルのタイトル (例: APK配布)",
        description="パネルの説明文 (例: 以下のメニューから選択してください)"
    )
    async def reward_panel(self, interaction: discord.Interaction, title: str, description: str):
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text="製作者_very(ぺにー)") # 画像に合わせてフッターを追加（不要なら消してください）
        await interaction.channel.send(embed=embed, view=RewardPanelView())
        await interaction.response.send_message("✅ パネルを設置しました。", ephemeral=True)

    @app_commands.command(name="reward_log_set", description="ログ送信先を設定します")
    async def reward_log_set(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = load_json(REWARD_CONFIG_FILE)
        gid = str(interaction.guild.id)
        if gid not in config: config[gid] = {}
        config[gid]["log_channel"] = channel.id
        save_json(REWARD_CONFIG_FILE, config)
        await interaction.response.send_message(f"✅ ログ送信先を {channel.mention} に設定しました。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Reward(bot))
