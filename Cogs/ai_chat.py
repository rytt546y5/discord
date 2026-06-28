import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
import json
import os
import io
import re

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
    """設定ファイルを保存する"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_api_key():
    """api_key.txtからキーを安全に読み込む"""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

# API設定
api_key = get_api_key()
model = None
if api_key:
    genai.configure(api_key=api_key)
    try:
        # あなたのリストで確認できた、404の出ないProモデル名称を使用
        model = genai.GenerativeModel(
            model_name='gemini-pro-latest', 
            system_instruction=(
                "あなたは、論理的思考と正確なコーディングにおいて世界最高峰の能力を持つ『Gemini Pro』です。"
                "経営者であるユーザーをサポートするため、一を聞いて十を知るような高度な回答を提供してください。"
                "1. PythonやDiscord.pyのコード生成は、最新の仕様に基づき、バグのない完璧なものを出力すること。"
                "2. 経営に関するアドバイスは、具体的かつ論理的な根拠を伴うこと。"
                "3. 回答は常に丁寧な日本語で行い、重要な部分は太字で強調してください。"
            )
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

    @app_commands.command(name="ai_set_channel", description="高知能Proモデルを専用チャンネルに連携します")
    @app_commands.describe(channel="AIとお喋りするチャンネル")
    @app_commands.default_permissions(administrator=True) # 管理者のみ
    async def ai_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not model:
            return await interaction.response.send_message("❌ AIの初期化に失敗しています。api_key.txtを確認してください。", ephemeral=True)
        
        config = load_config()
        config[str(interaction.guild.id)] = {"channel_id": channel.id}
        save_config(config)
        await interaction.response.send_message(f"✅ {channel.mention} を「最高知能顧問」チャンネルに設定しました。", ephemeral=True)

    @app_commands.command(name="ai_clear", description="AIの会話履歴（記憶）をリセットします")
    @app_commands.default_permissions(administrator=True)
    async def ai_clear(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid in self.chat_sessions:
            del self.chat_sessions[gid]
        await interaction.response.send_message("🧹 履歴をクリアし、知能をリフレッシュしました。", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Bot自身や model がない場合は無視
        if message.author.bot or not message.content or not model:
            return

        # チャンネルチェック
        config = load_config()
        target_id = config.get(str(message.guild.id), {}).get("channel_id")
        if message.channel.id != target_id:
            return

        # AIが回答を生成している間、タイピング表示を出す
        async with message.channel.typing():
            try:
                gid = str(message.guild.id)
                if gid not in self.chat_sessions:
                    self.chat_sessions[gid] = model.start_chat(history=[])

                # 無料枠の負荷を減らすため、直近の10往復分だけ履歴を保持
                if len(self.chat_sessions[gid].history) > 20:
                    self.chat_sessions[gid].history = self.chat_sessions[gid].history[-20:]

                # AIにメッセージを送信
                response = self.chat_sessions[gid].send_message(message.content)
                answer = response.text

                # Discordの2000文字制限への対応
                if len(answer) <= 2000:
                    await message.reply(answer)
                else:
                    # 長文はファイルとして送信
                    with io.BytesIO(answer.encode("utf-8")) as f:
                        await message.reply(
                            "📄 回答が高度な長文となったため、ファイルで出力しました。", 
                            file=discord.File(f, filename="pro_answer.txt")
                        )
            
            except Exception as e:
                err_text = str(e)
                if "429" in err_text:
                    await message.reply("⚠️ **1.5 Pro の無料枠制限**に達しました。最高知能を維持するため、1分ほど時間を空けてください。")
                else:
                    # エラーメッセージを短く丸めて送信
                    await message.reply(f"⚠️ AIエラーが発生しました。時間を置くか、`/ai_clear` を試してください。\n内容: `{err_text[:200]}`")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
