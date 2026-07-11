import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re

# =====================
# DATA
# =====================
DATA_FILE = "auto_response.json"

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# =====================
# COG
# =====================
class AutoResponse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="auto_add", description="自動返信ワードを追加します")
    @app_commands.describe(keyword="反応する言葉（それを含んでいると反応します）", response="AIが返信する言葉")
    @app_commands.default_permissions(administrator=True)
    async def add_response(self, interaction: discord.Interaction, keyword: str, response: str):
        data = load_data()
        gid = str(interaction.guild.id)
        
        if gid not in data:
            data[gid] = {}
        
        # キーワードを小文字化して登録（大文字小文字の差をなくすため）
        data[gid][keyword.lower()] = response
        save_data(data)
        
        embed = discord.Embed(title="✅ 自動返信登録完了", color=discord.Color.green())
        embed.add_field(name="キーワード", value=f"```{keyword}```", inline=False)
        embed.add_field(name="返信内容", value=f"```{response}```", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="auto_remove", description="自動返信ワードを削除します")
    @app_commands.describe(keyword="削除したいキーワード")
    @app_commands.default_permissions(administrator=True)
    async def remove_response(self, interaction: discord.Interaction, keyword: str):
        data = load_data()
        gid = str(interaction.guild.id)
        
        target = keyword.lower()
        if gid in data and target in data[gid]:
            del data[gid][target]
            save_data(data)
            await interaction.response.send_message(f"✅ 「{keyword}」への自動返信を削除しました。", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ 「{keyword}」は登録されていません。", ephemeral=True)

    @app_commands.command(name="auto_list", description="現在登録されている自動返信一覧を表示します")
    @app_commands.default_permissions(administrator=True)
    async def list_responses(self, interaction: discord.Interaction):
        data = load_data()
        gid = str(interaction.guild.id)
        
        if gid not in data or not data[gid]:
            return await interaction.response.send_message("現在登録されている自動返信はありません。", ephemeral=True)
        
        embed = discord.Embed(title="📋 自動返信リスト", color=discord.Color.blue())
        for kw, resp in data[gid].items():
            embed.add_field(name=kw, value=f"↳ {resp}", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Bot自身やDM、他サーバーは無視
        if message.author.bot or not message.guild:
            return

        data = load_data()
        gid = str(message.guild.id)
        
        if gid not in data:
            return

        # メッセージ内容を小文字化
        content = message.content.lower()

        # 登録されているキーワードが含まれているかチェック
        for keyword, response in data[gid].items():
            if keyword in content:
                # 指定の言葉を返信（メンションなし）
                await message.channel.send(response)
                return # 1つのメッセージにつき1つの反応だけにする

async def setup(bot):
    await bot.add_cog(AutoResponse(bot))
