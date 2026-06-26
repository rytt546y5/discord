import discord
from discord.ext import commands
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
STATUS = "Developer_very_"
FOOTER_TEXT = "Createby:@penyes114514_developer_"


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="$",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        print("Loading Cogs...")

        for file in os.listdir("./Cogs"):
            if file.endswith(".py") and not file.startswith("_"):
                try:
                    await self.load_extension(f"Cogs.{file[:-3]}")
                    print(f"Loaded: {file}")
                except Exception:
                    traceback.print_exc()

        # =====================
        # Persistent Views
        # =====================
        try:
            from Cogs.reward_views import RewardPanelView

            self.add_view(RewardPanelView())  # ⭐ reward永続化

            print("Persistent Views Loaded")

        except Exception:
            traceback.print_exc()

        try:
            await self.tree.sync()
            print("SYNC DONE")
        except Exception:
            traceback.print_exc()


bot = MyBot()


@bot.event
async def on_ready():
    print("起動成功👍")

    await bot.change_presence(
        activity=discord.Game(name=STATUS),
        status=discord.Status.online
    )

    print("Cogs:", list(bot.cogs.keys()))


@bot.tree.error
async def on_app_command_error(interaction, error):
    print("ERROR:", error)

    try:
        if interaction.response.is_done():
            await interaction.followup.send(f"エラー: {error}", ephemeral=True)
        else:
            await interaction.response.send_message(f"エラー: {error}", ephemeral=True)
    except:
        pass


bot.run(TOKEN)
