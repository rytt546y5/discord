import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
import json
import os
import io

# =====================
# 設定
# =====================
CONFIG_FILE = "ai_config.json"
KEY_FILE = "api_key.txt"

def load_config():
    """設定を読み込む"""
    if not os.path.exists(CONFIG_FILE): return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_config(data):
    """設定を保存する"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_api_key():
    """VPS内のapi_key.txtからキーを読み込む"""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

# APIの初期設定
api_key = get_api_key()
model = None

if api_key:
    genai.configure(api_key=api_key)
    try:
        # ご要望の最新モデル『2.0-Flash-Lite』を指定
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-lite', 
            system_instruction=(
                "あなたは『神の知能』を持つ経営顧問兼シニアエンジニアです。"
                "1. 回答は常に論理的で、経営者であるユーザーの利益を最大化する提案をしてください。"
                "2. プログラミングの質問には、最新のDiscord.py仕様に基づいた完璧なコードを提供してください。"
                "3. 前置きは不要です。結論から述べ、重要な部分は太字で強調してください。"
            )
        )
    except Exception as e:
        print(f"⚠️ AI初期化エラー: {e}")

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}

    @app_commands.command(name="ai_set_channel", description="最新2.0-Flash-Liteをチャンネルに連携します")
    @app_commands.default_permissions(administrator=True)
    async def ai_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not model:
            return await interaction.response.send_message("❌ APIキーが読み込めていないか、初期化に失敗しています。", ephemeral=True)
        
        config = load_config()
        config[str(interaction.guild.id)] = {"channel_id": channel.id}
        save_config(config)
        await interaction.response.send_message(f"✅ {channel.mention} で最新AI『2.0-Flash-Lite』を起動しました。", ephemeral=True)

    @app_commands.command(name="ai_clear", description="AIの記憶をリセットします")
    @app_commands.default_permissions(administrator=True)
    async def ai_clear(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid in self.sessions:
            del self.sessions[gid]
        await interaction.response.send_message("🧹 履歴をクリアし、知能をリフレッシュしました。", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content or not model:
            return

        config = load_config()
        if message.channel.id != config.get(str(message.guild.id), {}).get("channel_id"):
            return

        async with message.channel.typing():
            try:
                gid = str(message.guild.id)
                if gid not in self.sessions:
                    self.sessions[gid] = model.start_chat(history=[])

                # 履歴が長くなると制限にかかりやすいため、直近10往復(20メッセージ)に制限
                if len(self.sessions[gid].history) > 20:
                    self.sessions[gid].history = self.sessions[gid].history[-20:]

                # AIに送信
                response = self.sessions[gid].send_message(message.content)
                answer = response.text

                # Discord文字数制限対応
                if len(answer) <= 2000:
                    await message.reply(answer)
                else:
                    with io.BytesIO(answer.encode("utf-8")) as f:
                        await message.reply("📄 回答が長文（2000文字超）のため、ファイルとして出力しました。", file=discord.File(f, filename="answer.txt"))

            except Exception as e:
                err = str(e)
                if "429" in err:
                    await message.reply("⚠️ **最新モデルの無料枠制限**に達しました。1分ほど待つか、`/ai_clear` で履歴を整理してください。")
                else:
                    await message.reply(f"⚠️ エラーが発生しました。\n`{err[:200]}`")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
