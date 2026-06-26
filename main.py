import discord
from discord.ext import commands
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
STATUS = "Developer_very_"
FOOTER_TEXT = "Createby:@very_developer_"


# =====================
# BOT
# =====================
class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        print("Loading Cogs...")

        for filename in os.listdir("./Cogs"):
            if filename.endswith(".py") and not filename.startswith("_"):
                try:
                    await self.load_extension(f"Cogs.{filename[:-3]}")
                    print(f"Loaded: {filename}")
                except Exception:
                    print(f"Failed: {filename}")
                    traceback.print_exc()

        # =====================
        # PERSISTENT VIEWS（ここが重要）
        # =====================
        try:
            from Cogs.achievement import AchievementView
            from Cogs.giveaway import GiveawayView
            from Cogs.verify import VerifyView
            from Cogs.ticket import TicketView, TicketCloseView
            from Cogs.reward_views import RewardPanelView  # ←追加

            self.add_view(AchievementView())
            self.add_view(GiveawayView(message_id=0))
            self.add_view(VerifyView(0))
            self.add_view(TicketView(0))
            self.add_view(TicketCloseView())

            # ⭐ Reward追加
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
# INTENTS
# =====================
intents = discord.Intents.all()

bot = MyBot(
    command_prefix="$",
    intents=intents,
    help_command=None
)


# =====================
# READY
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
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    print("=" * 50)
    print("APP COMMAND ERROR")
    traceback.print_exception(type(error), error, error.__traceback__)
    print("=" * 50)

    try:
        if interaction.response.is_done():
            await interaction.followup.send(f"エラー: {error}", ephemeral=True)
        else:
            await interaction.response.send_message(f"エラー: {error}", ephemeral=True)
    except:
        pass


# =====================
# RUN
# =====================
bot.run(TOKEN)
