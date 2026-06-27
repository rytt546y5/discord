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
        # あなたのリストで確実に動作する名前「gemini-flash-latest」を指定
        # 「シャバさ」を消すために、命令（System Instruction）を最強レベルに強化
        model = genai.GenerativeModel(
            model_name='gemini-flash-latest', 
            system_instruction=(
                "あなたは、年収数千万円クラスの超エリート経営コンサルタント兼、天才フルスタックエンジニアです。"
                "【思考プロトコル】"
                "1. ユーザーの質問に対し、表面的な回答ではなく、その裏にある意図を汲み取って回答してください。"
                "2. プログラミングの依頼には、バグがなく、効率的で、美しいPythonコードを提供してください。"
                "3. 経営の相談には、具体的で、即戦力となる戦略をステップバイステップで提示してください。"
                "4. 常に深呼吸して、論理的に最も優れた答えを導き出してから発言してください。"
                "【回答スタイル】"
                "- 無駄な挨拶は省き、結論から述べること。"
                "- 重要なキーワードは太字で強調すること。"
                "- 専門家としての威厳を持ちつつ、丁寧な日本語を使うこと。"
            )
        )
    except Exception as e:
        print(f"⚠️ 初期化失敗: {e}")

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_sessions = {}

    @app_commands.command(name="ai_set_channel", description="AIが自動回答する専用チャンネルを設定します")
    @app_commands.default_permissions(administrator=True)
    async def ai_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not model:
            return await interaction.response.send_message("❌ AIの初期化に失敗しています。api_key.txtを確認してください。", ephemeral=True)
        config = load_config()
        config[str(interaction.guild.id)] = {"channel_id": channel.id}
        save_config(config)
        await interaction.response.send_message(f"✅ {channel.mention} を「超知能AI助手」チャンネルに設定しました。", ephemeral=True)

    @app_commands.command(name="ai_clear", description="会話履歴をクリアして知能をリフレッシュします")
    @app_commands.default_permissions(administrator=True)
    async def ai_clear(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid in self.chat_sessions:
            del self.chat_sessions[gid]
        await interaction.response.send_message("🧹 記憶をリセットしました。知能がリフレッシュされました。", ephemeral=True)

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
                        await message.reply("📄 プロ級の長文回答となったため、ファイルで出力します。", file=discord.File(f, filename="answer.txt"))
            
            except Exception as e:
                err_text = str(e)
                if "429" in err_text:
                    await message.reply("⚠️ 現在、Google側の回数制限がかかっています。1分ほど待ってから再度お試しください。")
                else:
                    await message.reply(f"⚠️ エラーが発生しました。`/ai_clear` で解決する場合があります。\n内容: `{err_text[:500]}`")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
