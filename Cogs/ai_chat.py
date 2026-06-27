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

def get_api_key():
    """api_key.txtからキーを読み込む"""
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
    # 最も安定し、かつ高速な 1.5 Flash を使用
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=(
            "あなたは経営・取引系Discordサーバーの専属AI助手です。"
            "プログラミング（Python, Discord.py）の知識が非常に高く、正確なコードを提案します。"
            "回答は論理的かつ丁寧に行い、経営者であるユーザーを全力でサポートしてください。"
            "重要な箇所は太字を使い、読みやすい日本語で回答してください。"
        )
    )
else:
    model = None
    print("⚠️ [AI Chat] api_key.txt が見つからないためAIを無効化します。")

# =====================
# COG
# =====================
class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_sessions = {} # サーバーごとの履歴

    @app_commands.command(name="ai_set_channel", description="AIが自動回答する専用チャンネルを設定します")
    @app_commands.describe(channel="AIチャット用にするチャンネル")
    @app_commands.default_permissions(administrator=True) # 管理者のみ
    async def ai_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not model:
            return await interaction.response.send_message("❌ APIキーが読み込めていません。", ephemeral=True)
        
        config = load_config()
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

        config = load_config()
        target_id = config.get(str(message.guild.id), {}).get("channel_id")

        if message.channel.id != target_id:
            return

        # AIが回答を生成中であることを示す（入力中...）
        async with message.channel.typing():
            try:
                gid = str(message.guild.id)
                if gid not in self.chat_sessions:
                    self.chat_sessions[gid] = model.start_chat(history=[])

                # AIへメッセージ送信
                response = self.chat_sessions[gid].send_message(message.content)
                answer = response.text

                # Discord文字数制限(2000)対応
                if len(answer) <= 2000:
                    await message.reply(answer)
                else:
                    # 2000文字を超える場合はファイル出力
                    with io.BytesIO(answer.encode("utf-8")) as f:
                        await message.reply(
                            "📄 回答が長文のため、ファイルとして出力しました。",
                            file=discord.File(f, filename="ai_answer.txt")
                        )

            except Exception as e:
                # エラーハンドリング
                err_str = str(e)
                if "404" in err_str:
                    await message.reply("⚠️ モデルが見つかりません。設定を確認してください。")
                elif "quota" in err_str.lower():
                    await message.reply("⚠️ 無料枠の制限に達しました。しばらく待ってからお試しください。")
                else:
                    await message.reply(f"⚠️ エラーが発生しました。`/ai_clear` で解決する場合があります。\n内容: `{err_str}`")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
