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

def load_json(file):
    if not os.path.exists(file): return {}
    with open(file, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_json(file, data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_api_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

api_key = get_api_key()
model = None

if api_key:
    genai.configure(api_key=api_key)
    # あなたの環境で404を出さず、かつ最強知能を呼び出すための特定名称
    # 'models/gemini-1.5-pro-latest' を試します。
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-pro-latest', 
            system_instruction=(
                "あなたは世界最高クラスのAI「Gemini 1.5 Pro」です。経営者であるユーザーに対し、"
                "妥協のない、最高精度の回答を提供してください。特にPythonコードの生成においては、"
                "プロ級の品質を保証してください。日本語で論理的に回答してください。"
            )
        )
    except:
        # もし上記がダメなら、標準の名称にフォールバック
        model = genai.GenerativeModel(model_name='gemini-1.5-pro')

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_sessions = {}

    @app_commands.command(name="ai_set_channel", description="最高知能Proを連携します")
    @app_commands.default_permissions(administrator=True)
    async def ai_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not model: return await interaction.response.send_message("❌ AI初期化失敗", ephemeral=True)
        config = load_json(CONFIG_FILE)
        config[str(interaction.guild.id)] = {"channel_id": channel.id}
        save_json(CONFIG_FILE, config)
        await interaction.response.send_message(f"✅ {channel.mention} で 1.5 Pro を起動しました。", ephemeral=True)

    @app_commands.command(name="ai_clear", description="記憶のリセット")
    @app_commands.default_permissions(administrator=True)
    async def ai_clear(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid in self.chat_sessions: del self.chat_sessions[gid]
        await interaction.response.send_message("🧹 履歴をクリアしました。", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content or not model: return

        config = load_json(CONFIG_FILE)
        target_id = config.get(str(message.guild.id), {}).get("channel_id")
        if message.channel.id != target_id: return

        async with message.channel.typing():
            try:
                gid = str(message.guild.id)
                if gid not in self.chat_sessions:
                    self.chat_sessions[gid] = model.start_chat(history=[])

                # 【知能維持のための調整】
                # Proは情報量が多いので、履歴は直近10往復(20件)に絞ってエラーを防ぐ
                if len(self.chat_sessions[gid].history) > 20:
                    self.chat_sessions[gid].history = self.chat_sessions[gid].history[-20:]

                response = self.chat_sessions[gid].send_message(message.content)
                answer = response.text

                if len(answer) <= 2000:
                    await message.reply(answer)
                else:
                    with io.BytesIO(answer.encode("utf-8")) as f:
                        await message.reply("📄 高性能回答をファイル化しました。", file=discord.File(f, filename="pro_answer.txt"))
            
            except Exception as e:
                err = str(e)
                if "429" in err:
                    await message.reply("⚠️ **1.5 Pro の無料枠制限（1分間2回まで）**に達しました。最高知能を維持するため、少し時間を空けてください。")
                elif "404" in err:
                    await message.reply("⚠️ モデル名が見つかりません。環境に合わせて調整が必要です。")
                else:
                    await message.reply(f"⚠️ エラー: `{err[:100]}`")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
