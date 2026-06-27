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

# モデルの初期化（429エラー回避のため、最も安定した 1.5-flash を使用）
model = None
if api_key:
    genai.configure(api_key=api_key)
    # 'gemini-1.5-flash' は世界中で最も安定して無料枠が提供されている名称です
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash', 
            system_instruction="あなたは優秀なAI助手です。日本語で丁寧に応答してください。"
        )
    except Exception as e:
        print(f"⚠️ 初期化エラー: {e}")

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_sessions = {}

    @app_commands.command(name="ai_set_channel", description="AIが自動回答する専用チャンネルを設定します")
    @app_commands.default_permissions(administrator=True)
    async def ai_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not model:
            return await interaction.response.send_message("❌ AIが正しく初期化されていません。APIキーを確認してください。", ephemeral=True)
        config = load_json(CONFIG_FILE)
        config[str(interaction.guild.id)] = {"channel_id": channel.id}
        save_config(config)
        await interaction.response.send_message(f"✅ {channel.mention} をAIチャットチャンネルに設定しました。", ephemeral=True)

    @app_commands.command(name="ai_clear", description="AIの会話履歴をリセットします")
    @app_commands.default_permissions(administrator=True)
    async def ai_clear(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid in self.chat_sessions:
            del self.chat_sessions[gid]
        await interaction.response.send_message("🧹 会話履歴をクリアしました。", ephemeral=True)

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
                        await message.reply("📄 回答が長いため、ファイルでお送りします。", file=discord.File(f, filename="answer.txt"))
            
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    # 429エラー（Quota制限）が出た場合、自動で別モデルへの切り替えを試みる（裏技）
                    await message.reply("⚠️ 現在、Google側の無料枠制限がかかっています。1分ほど待ってから再度お試しください。")
                else:
                    await message.reply(f"⚠️ エラーが発生しました。`/ai_clear` をお試しください。\n`{error_msg}`")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
