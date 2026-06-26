import discord
from discord.ext import commands
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
STATUS = "Developer_very_"


# =====================
# BOT
# =====================
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="$",
            intents=intents,
            help_command=None
        )

        # ⭐ vending.py 対策（絶対必要）
        self.embed_footer = "Createby:@penyes114514_developer_"

    async def setup_hook(self):
        print("Loading Cogs...")

        # =====================
        # COG LOAD
        # =====================
        for file in os.listdir("./Cogs"):
            if file.endswith(".py") and not file.startswith("_"):

                # ❌ reward_views は絶対にCogとして読み込まない
                if file == "reward_views.py":
                    continue

                try:
                    await self.load_extension(f"Cogs.{file[:-3]}")
                    print(f"Loaded: {file}")
                except Exception:
                    print(f"Failed: {file}")
                    traceback.print_exc()

        # =====================
        # PERSISTENT VIEWS
        # =====================
        try:
            from Cogs.reward_views import RewardPanelView
            self.add_view(RewardPanelView())
            print("Persistent Views Loaded")

        except Exception:
            traceback.print_exc()

        # =====================
        # SYNC
        # =====================
        try:
            await self.tree.sync()
            print("SYNC DONE")
        except Exception:
            traceback.print_exc()


# =====================
# BOT INSTANCE
# =====================
bot = MyBot()


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

    print("Cogs:", list(bot.cogs.keys()))
    print("Commands:", [c.name for c in bot.tree.get_commands()])


# =====================
# ERROR HANDLER
# =====================
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    print("=" * 40)
    print("APP COMMAND ERROR")
    traceback.print_exception(type(error), error, error.__traceback__)
    print("=" * 40)

    try:
        msg = f"エラー: {error}"

        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    except Exception:
        pass


# =====================
# RUN
# =====================
if not TOKEN:
    raise RuntimeError("TOKENが環境変数に設定されていません")

bot.run(TOKEN)
