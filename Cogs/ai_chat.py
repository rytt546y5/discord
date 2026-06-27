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

def load_config():
    """設定ファイルを読み込む"""
    if not os.path.exists(CONFIG_FILE): return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_config(data):
    """設定ファイルを保存する（エラーの起きていた箇所を修正）"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_api_key():
    """api_key.txtからキーを読み込む"""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

# APIキーの初期設定
api_key = get_api_key()
model = None
if api_key:
    genai.configure(api_key=api_key)
    try:
        # 安定の1.5-flashを使用
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction="あなたは経営サーバーの優秀なAI助手です。日本語で回答してください。"
        )
    except Exception as e:
        print(f"⚠️ AI初期化エラー: {e}")

# =====================
# COG
# =====================
class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_sessions = {}

    @app_commands.command(name="ai_set_channel", description="AIが自動回答する専用チャンネルを設定します")
    @app_commands.describe(channel="AIチャット用にするチャンネル")
    @app_commands.default_permissions(administrator=True)
    async def ai_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not model:
            return await interaction.response.send_message("❌ APIキーが読み込めていないか、AIの初期化に失敗しています。", ephemeral=True)
        
        config = load_config()
        config[str(interaction.guild.id)] = {"channel_id": channel.id}
        save_config(config) # ここでエラーが起きていたのを修正しました
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

        config = load_config()
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
                        await message.reply("📄 回答が長いためファイルで出力しました。", file=discord.File(f, filename="answer.txt"))
            
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    await message.reply("⚠️ 現在、Googleの無料枠制限がかかっています。1分ほど待ってから再度お試しください。")
                else:
                    await message.reply(f"⚠️ エラーが発生しました。\n`{error_msg}`")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
