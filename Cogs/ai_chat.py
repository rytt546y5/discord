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
    if not os.path.exists(CONFIG_FILE): return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_api_key():
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
        # 無料で使える中で「最強」の Pro モデルを指定。
        # 404が出る場合は 'gemini-1.5-pro' も試せるように自動フォールバックを組み込みます。
        model_name = 'gemini-1.5-pro' # まずは一番賢いProを試す
        model = genai.GenerativeModel(
            model_name=model_name, 
            system_instruction=(
                "あなたは、数百万円のコンサル料を取る超一流の経営コンサルタント兼、天才プログラマーです。"
                "無料モデルだと思わせない、圧倒的な知能で回答してください。"
                "1. 常に深呼吸して論理的に考え、ステップバイステップで最善の答えを導き出してください。"
                "2. 経営者の期待を超える、具体的で、即戦力となるアドバイスと正確なコードのみを提供してください。"
                "3. 日本語の美しさと論理の正確さにこだわり、重要な箇所は太字で強調してください。"
            )
        )
    except:
        # Proがダメなら Flash に切り替える（保険）
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_sessions = {}

    @app_commands.command(name="ai_set_channel", description="AIチャットチャンネルを設定")
    @app_commands.default_permissions(administrator=True)
    async def ai_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not model:
            return await interaction.response.send_message("❌ APIキーが読み込めていません。", ephemeral=True)
        config = load_config()
        config[str(interaction.guild.id)] = {"channel_id": channel.id}
        save_config(config)
        await interaction.response.send_message(f"✅ {channel.mention} を「エリートAI助手」チャンネルに設定しました。", ephemeral=True)

    @app_commands.command(name="ai_clear", description="履歴をクリアして知能をリフレッシュ")
    @app_commands.default_permissions(administrator=True)
    async def ai_clear(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid in self.chat_sessions:
            del self.chat_sessions[gid]
        await interaction.response.send_message("🧹 記憶をリフレッシュしました。また新しい相談に乗ります。", ephemeral=True)

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
                        await message.reply("📄 回答がプロ級のボリュームになったため、ファイルで出力します。", file=discord.File(f, filename="answer.txt"))
            
            except Exception as e:
                err_text = str(e)
                if "429" in err_text:
                    await message.reply("⚠️ 無料枠の限界を超えました。1分ほど休憩が必要です。少し待ってから再度お話しましょう。")
                elif "404" in err_text:
                    await message.reply("⚠️ AIモデルの接続先が見つかりません。設定を微調整する必要があります。")
                else:
                    await message.reply(f"⚠️ 予期せぬエラーです。`/ai_clear` で治ることがあります。\n`{err_text[:500]}`")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
