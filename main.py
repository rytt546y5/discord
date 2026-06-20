import discord
from discord.ext import commands
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

STATUS = "Developer_very_"
FOOTER_TEXT = "Developer_べりー"

# =====================
# GUILD ID（ここ重要）
# =====================
GUILD_ID = 1517761896390983750  # ←ここにサーバーID入れる


# =====================
# BOT CLASS
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

        # 💥 guild sync（即時反映）
        guild = discord.Object(id=GUILD_ID)
        await self.tree.sync(guild=guild)

        print("SYNC DONE (GUILD MODE)")


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
    print("❌ ERROR:", error)
    import traceback
    traceback.print_exc()

    try:
        await interaction.response.send_message(
            "エラーが発生しました",
            ephemeral=True
        )
    except:
        pass


# =====================
# RUN
# =====================
bot.run(TOKEN)
