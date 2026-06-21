import discord
from discord.ext import commands
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

STATUS = "Developer_very!_"
GUILD_ID = 1517761896390983750


# =====================
# BOT CLASS
# =====================
class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 💥ここで必ず初期化（重要）
        self.embed_footer = "Createby:@keru_developer_"

    async def setup_hook(self):
        print("Loading Cogs...")

        # =====================
        # COG LOAD
        # =====================
        for filename in os.listdir("./Cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"Cogs.{filename[:-3]}")
                    print(f"Loaded: {filename}")
                except Exception:
                    print(f"Failed: {filename}")
                    traceback.print_exc()

        guild = discord.Object(id=GUILD_ID)

        # =====================
        # 💥SYNC（安定版）
        # =====================

        # ※clear_commandsは不安定なので削除
        await self.tree.sync(guild=guild)

        print("SYNC DONE (PRO MODE)")


# =====================
# INTENTS
# =====================
intents = discord.Intents.all()
bot = MyBot(command_prefix="$", intents=intents, help_command=None)


# =====================
# READY EVENT
# =====================
@bot.event
async def on_ready():
    print("起動成功👍")

    await bot.change_presence(
        activity=discord.Game(name=STATUS),
        status=discord.Status.online
    )

    print("COGS:", list(bot.cogs.keys()))
    print("COMMANDS:", [c.name for c in bot.tree.get_commands()])


# =====================
# ERROR HANDLER
# =====================
@bot.tree.error
async def on_app_command_error(interaction, error):
    print("=" * 50)
    print("APP COMMAND ERROR")
    traceback.print_exception(type(error), error, error.__traceback__)
    print("=" * 50)

    try:
        await interaction.response.send_message(
            f"エラー: {error}",
            ephemeral=True
        )
    except:
        pass


# =====================
# RUN
# =====================
bot.run(TOKEN)
