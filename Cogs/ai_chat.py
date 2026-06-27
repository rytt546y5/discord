import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
import json
import os
import io
import datetime

# =====================
# 設定・パス
# =====================
CONFIG_FILE = "ai_config.json"
KEY_FILE = "api_key.txt"

def load_json(file):
    if not os.path.exists(file): return {}
    with open(file, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# APIキーの読み込み
api_key = None
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "r", encoding="utf-8") as f:
        api_key = f.read().strip()

if api_key:
    genai.configure(api_key=api_key)
    # リストにある最新の 'gemini-2.0-flash' を使用します
    model = genai.GenerativeModel(
        model_name='gemini-2.0-flash', 
        system_instruction=(
            "あなたは経営・取引系Discordサーバーの非常に優秀なAI助手です。"
            "最新のAIモデルとして、プログラミング（Python, Discord.py）の回答は完璧に行います。"
            "経営者であるユーザーの指示を正確に理解し、論理的かつ丁寧な日本語でサポートしてください。"
            "重要な箇所は太字を使い、コードはマークダウン形式で提供してください。"
        )
    )
else:
    model = None

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_sessions = {}

    @app_commands.command(name="ai_set_channel", description="AIが自動回答する専用チャンネルを設定します")
    @app_commands.default_permissions(administrator=True)
    async def ai_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not model:
            return await interaction.response.send_message("❌ APIキーが読み込めていないか、初期化に失敗しています。", ephemeral=True)
        config = load_json(CONFIG_FILE)
        config[str(interaction.guild.id)] = {"channel_id": channel.id}
        save_json(CONFIG_FILE, config)
        await interaction.response.send_message(f"✅ {channel.mention} を最新AIチャットチャンネルに設定しました。", ephemeral=True)

    @app_commands.command(name="ai_clear", description="AIの会話履歴をリセットします")
    @app_commands.default_permissions(administrator=True)
    async def ai_clear(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid in self.chat_sessions:
            del self.chat_sessions[gid]
        await interaction.response.send_message("🧹 履歴をクリアしました。新しい会話を始めましょう。", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content or not model:
            return

        config = load_json(CONFIG_FILE)
        target_id = config.get(str(message.guild.id), {}).get("channel_id")
        if message.channel.id != target_id:
            return

        async with message.channel.typing():
            try:
                gid = str(message.guild.id)
                if gid not in self.chat_sessions:
                    self.chat_sessions[gid] = model.start_chat(history=[])

                response = self.chat_sessions[gid].send_message(message.content)
                answer = response.text

                if len(answer) <= 2000:
                    await message.reply(answer)
                else:
                    with io.BytesIO(answer.encode("utf-8")) as f:
                        await message.reply("📄 回答が非常に長いため、ファイルで出力しました。", file=discord.File(f, filename="answer.txt"))
            except Exception as e:
                await message.reply(f"⚠️ AIエラーが発生しました。履歴が長すぎる場合は `/ai_clear` を試してください。\n`{e}`")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
