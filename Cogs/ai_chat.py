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
pro_model = None
flash_model = None

if api_key:
    genai.configure(api_key=api_key)
    # メインの知能 (Pro)
    pro_model = genai.GenerativeModel(
        model_name='gemini-pro-latest',
        system_instruction="あなたは最高知能を持つ顧問です。論理的かつ専門的な回答をしてください。"
    )
    # バックアップの知能 (Flash) - 429エラー時に使用
    flash_model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction="あなたは優秀な助手です。現在Proモデルが制限中のため、代役として簡潔に回答します。"
    )

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}

    @app_commands.command(name="ai_set_channel", description="高知能AIをチャンネルに連携します")
    @app_commands.default_permissions(administrator=True)
    async def ai_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = load_config()
        config[str(interaction.guild.id)] = {"channel_id": channel.id}
        save_config(config)
        await interaction.response.send_message(f"✅ {channel.mention} をAIチャンネルに設定しました。", ephemeral=True)

    @app_commands.command(name="ai_clear", description="会話履歴をクリアします")
    @app_commands.default_permissions(administrator=True)
    async def ai_clear(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid in self.sessions: del self.sessions[gid]
        await interaction.response.send_message("🧹 履歴をクリアしました。", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content or not pro_model: return
        config = load_config()
        if message.channel.id != config.get(str(message.guild.id), {}).get("channel_id"): return

        async with message.channel.typing():
            gid = str(message.guild.id)
            if gid not in self.sessions:
                self.sessions[gid] = {"pro": pro_model.start_chat(history=[]), "flash": flash_model.start_chat(history=[])}

            try:
                # まずは最高知能(Pro)で試行
                response = self.sessions[gid]["pro"].send_message(message.content)
                answer = response.text
            except Exception as e:
                if "429" in str(e):
                    # Proが制限中なら、爆速のFlashで即座にカバー
                    try:
                        response = self.sessions[gid]["flash"].send_message(f"【至急】Proが制限中のため代打で答えてください: {message.content}")
                        answer = f"⚠️(Pro制限中/Flash代行)\n{response.text}"
                    except:
                        answer = "⚠️ AIの無料枠が完全に上限に達しました。1分ほどお待ちください。"
                else:
                    answer = f"⚠️ エラーが発生しました: {str(e)[:100]}"

            if len(answer) <= 2000:
                await message.reply(answer)
            else:
                with io.BytesIO(answer.encode("utf-8")) as f:
                    await message.reply("📄 回答が長いためファイルで送信します。", file=discord.File(f, filename="ai_answer.txt"))

async def setup(bot):
    await bot.add_cog(AIChat(bot))
