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

# API設定：最も枠が安定している gemini-1.5-flash に強制固定
api_key = None
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "r", encoding="utf-8") as f:
        api_key = f.read().strip()

model = None
if api_key:
    genai.configure(api_key=api_key)
    # 2.0やLiteで「Limit 0」が出る場合でも、1.5-flashなら動く確率が非常に高いです
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash', 
        system_instruction="あなたは優秀な経営・開発助手です。日本語で簡潔かつ正確に回答してください。"
    )

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}

    @app_commands.command(name="ai_set_channel", description="AIチャットを設定（管理者のみ）")
    @app_commands.default_permissions(administrator=True)
    async def ai_set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not model: return await interaction.response.send_message("❌ API初期化失敗", ephemeral=True)
        config = load_config()
        config[str(interaction.guild.id)] = {"channel_id": channel.id}
        save_config(config)
        await interaction.response.send_message(f"✅ {channel.mention} をAIチャンネルに設定しました。", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content or not model: return
        config = load_config()
        if message.channel.id != config.get(str(message.guild.id), {}).get("channel_id"): return

        async with message.channel.typing():
            try:
                gid = str(message.guild.id)
                if gid not in self.sessions:
                    self.sessions[gid] = model.start_chat(history=[])
                
                # 履歴が長くなると無料枠制限に触れるため、短く維持
                if len(self.sessions[gid].history) > 10:
                    self.sessions[gid].history = self.sessions[gid].history[-10:]

                response = self.sessions[gid].send_message(message.content)
                await message.reply(response.text[:2000])

            except Exception as e:
                err = str(e)
                if "429" in err:
                    await message.reply("⚠️ 現在、Google側の無料枠（1分間の回数制限）に達しています。1分ほど待ってから話しかけてください。")
                elif "500" in err:
                    await message.reply("⚠️ Googleサーバー側でエラーが起きています。少し時間をおいてください。")
                else:
                    await message.reply(f"⚠️ 申し訳ありません、一時的に回答できません。\n内容: `{err[:100]}`")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
