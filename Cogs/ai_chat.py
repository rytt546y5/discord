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

api_key = get_api_key()
model = None

if api_key:
    genai.configure(api_key=api_key)
    try:
        # あなたのリストにある確実なProモデル「gemini-pro-latest」を指定
        model = genai.GenerativeModel(
            model_name='gemini-pro-latest', 
            system_instruction=(
                "あなたは、論理的思考とコーディングにおいて最高水準の能力を持つ『Gemini Pro』です。"
                "Flashモデルのような簡略化された回答は厳禁です。一通のメッセージで、"
                "経営者が求める深い洞察と、エンジニアが納得する正確なコードを提供してください。"
                "回答前に内部で3回思考を重ね、最も効率的でバグのない結論を日本語で出力してください。"
            )
        )
    except Exception as e:
        print(f"⚠️ 初期化エラー: {e}")

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_sessions = {}

    @app_commands.command(name="ai_set_channel", description="高知能Proモデルを連携します")
    @app_commands.default_permissions(administrator=True)
    async def ai_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not model: return await interaction.response.send_message("❌ AI初期化失敗。キーを確認してください。", ephemeral=True)
        config = load_config()
        config[str(interaction.guild.id)] = {"channel_id": channel.id}
        save_config(config)
        await interaction.response.send_message(f"✅ {channel.mention} で『Pro知能』を起動しました。", ephemeral=True)

    @app_commands.command(name="ai_clear", description="会話履歴をクリアします")
    @app_commands.default_permissions(administrator=True)
    async def ai_clear(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid in self.chat_sessions: del self.chat_sessions[gid]
        await interaction.response.send_message("🧹 履歴をクリアし、知能をリフレッシュしました。", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content or not model: return

        config = load_config()
        target_id = config.get(str(message.guild.id), {}).get("channel_id")
        if message.channel.id != target_id: return

        async with message.channel.typing():
            try:
                gid = str(message.guild.id)
                if gid not in self.chat_sessions:
                    self.chat_sessions[gid] = model.start_chat(history=[])

                # 履歴が長くなると無料枠のトークン制限に引っかかるため、直近8往復(16件)に制限
                if len(self.chat_sessions[gid].history) > 16:
                    self.chat_sessions[gid].history = self.chat_sessions[gid].history[-16:]

                response = self.chat_sessions[gid].send_message(message.content)
                answer = response.text

                if len(answer) <= 2000:
                    await message.reply(answer)
                else:
                    with io.BytesIO(answer.encode("utf-8")) as f:
                        await message.reply("📄 高性能回答が長文となったため、ファイルで出力しました。", file=discord.File(f, filename="pro_answer.txt"))
            
            except Exception as e:
                err = str(e)[:1500]
                if "429" in err:
                    await message.reply("⚠️ **Proモデルの無料枠制限**に達しました。1分ほど時間を空けてください。")
                else:
                    await message.reply(f"⚠️ AIエラー: `{err}`")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
