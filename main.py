import discord
from discord.ext import commands
from discord import app_commands
import os
import traceback
from dotenv import load_dotenv
from dotenv import load_dotenv
import os

load_dotenv()

from datetime import datetime, timezone

# ★envファイルからBOTのトークンを読み込む
token = os.getenv('TOKEN')

# BOTのステータスを設定
STATUS = "Developer_very_"

# BOTフロッターを設定(とりあえず自分の名前)
FOOTER_TEXT = "ぺにー「べりー」"



# ここからしたはいじらない
# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)

async def load_cogs():

    bot.embed_footer = FOOTER_TEXT

    for filename in os.listdir("./Cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"Cogs.{filename[:-3]}")

    await bot.tree.sync()

bot.setup_hook = load_cogs

@bot.event
async def on_ready():
    print("起動に成功しました👍🏻.")
    await bot.change_presence(activity=discord.Game(name=STATUS), status=discord.Status.idle)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        print(f"{interaction.user}によるコマンド({interaction.command.name})の実行がブロックされました。")
        return
    print(error)
    traceback.print_exc()

@@bot.event
async def on_ready():
    if not hasattr(bot, "synced"):
        await bot.tree.sync()
        bot.synced = True
        print("SYNC DONE")
bot.run(token)
