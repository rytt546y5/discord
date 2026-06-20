import discord
from discord.ext import commands
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

# =====================
# ENV
# =====================
TOKEN = os.getenv("TOKEN")

STATUS = "Developer_very_"
FOOTER_TEXT = "Developer_べりー"

# =====================
# BOT CLASS（重要）
# =====================
class MyBot(commands.Bot):
    async def setup_hook(self):
        self.embed_footer = FOOTER_TEXT

        print("Loading Cogs...")

        for filename in os.listdir("./Cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"Cogs.{filename[:-3]}")
                    print(f"Loaded: {filename}")
                except Exception as e:
                    print(f"Failed: {filename}")
                    print(e)

        await self.tree.sync()
        print("SYNC DONE")

# =====================
# BOT INIT
# =====================
intents = discord.Intents.all()
bot = MyBot(command_prefix="$", intents=intents, help_command=None)

# =====================
# READY EVENT
# =====================
@bot.event
async def on_ready():
    print("起動に成功しました👍🏻.")

    await bot.change_presence(
        activity=discord.Game(name=STATUS),
        status=discord.Status.idle
    )

    print("COGS:", list(bot.cogs.keys()))
    print("COMMANDS:", [c.name for c in bot.tree.get_commands()])

# =====================
# ERROR HANDLER
# =====================
@bot.tree.error
async def on_app_command_error(interaction, error):
    print("ERROR:", error)
    traceback.print_exc()

# =====================
# RUN
# =====================
bot.run(TOKEN)
