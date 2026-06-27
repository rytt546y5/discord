import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
import json
import os
import io

# =====================
# 設定・パス
# =====================
CONFIG_FILE = "ai_config.json"
KEY_FILE = "api_key.txt" # APIキーを保存したテキストファイル

def get_api_key():
    """サーバー上のファイルからAPIキーを安全に読み込む"""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def load_config():
    if not os.path.exists(CONFIG_FILE): return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# APIの初期設定
api_key = get_api_key()
if api_key:
    genai.configure(api_key=api_key)
    # 経営系サーバーに特化したシステム命令（性格付け）
    model = genai.GenerativeModel(
        model_name='gemini-1.5-pro',
        system_instruction=(
            "あなたは経営・取引系Discordサーバーの専属AI助手です。"
            "プログラミング（特にPython, Discord.py）の専門知識が非常に高く、正確で実用的なコードを提供します。"
            "回答は常に論理的かつ丁寧で、経営者であるユーザーを強力にサポートしてください。"
            "コードを提示する際はマークダウン形式を使い、重要なポイントは太字にしてください。"
        )
    )
else:
    model = None
    print("⚠️ [AI Chat] api_key.txt が見つからないため、AI機能は無効化されています。")

# =====================
# COG
# =====================
class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_sessions = {} # サーバーごとの会話履歴

    @app_commands.command(name="ai_set_channel", description="AIが自動回答する専用チャンネルを設定します")
    @app_commands.describe(channel="AIチャット用にするチャンネル")
    @app_commands.default_permissions(administrator=True)
    async def ai_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not model:
            return await interaction.response.send_message("❌ APIキーが設定されていないため、この機能は使えません。", ephemeral=True)
        
        config = load_config()
        config[str(interaction.guild.id)] = {"channel_id": channel.id}
        save_config(config)
        await interaction.response.send_message(f"✅ {channel.mention} をAIチャットチャンネルに設定しました。", ephemeral=True)

    @app_commands.command(name="ai_clear", description="AIの会話履歴をリセットしてリフレッシュします")
    @app_commands.default_permissions(administrator=True)
    async def ai_clear(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid in self.chat_sessions:
            del self.chat_sessions[gid]
        await interaction.response.send_message("🧹 会話履歴をリセットしました。", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # 除外条件
        if message.author.bot or not message.content or not model:
            return

        config = load_config()
        target_id = config.get(str(message.guild.id), {}).get("channel_id")

        # 指定チャンネル以外は無視
        if message.channel.id != target_id:
            return

        # AIのタイピング表示
        async with message.channel.typing():
            try:
                gid = str(message.guild.id)
                # セッションがなければ作成
                if gid not in self.chat_sessions:
                    self.chat_sessions[gid] = model.start_chat(history=[])

                # AIにメッセージ送信
                response = self.chat_sessions[gid].send_message(message.content)
                answer = response.text

                # Discord制限（2000文字）への対応
                if len(answer) <= 2000:
                    await message.reply(answer)
                else:
                    # 非常に長い場合は、HTMLログの技術を応用してテキストファイルで送信
                    with io.BytesIO(answer.encode("utf-8")) as f:
                        await message.reply(
                            "📄 回答が長文（2000文字超）のため、ファイルとして出力しました。ダウンロードしてご確認ください。",
                            file=discord.File(f, filename="ai_answer.txt")
                        )

            except Exception as e:
                # エラー（履歴が長すぎる等）が起きた際の親切な通知
                error_msg = str(e)
                if "quota" in error_msg.lower():
                    await message.reply("⚠️ 無料枠の制限に達しました。少し時間を置いてから再度お試しください。")
                else:
                    await message.reply(f"⚠️ エラーが発生しました。`/ai_clear` で履歴を消すと直る場合があります。\n`{error_msg}`")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
