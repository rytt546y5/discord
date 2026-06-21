import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

GUILD_ID = 1517761896390983750  # 開発サーバーID


class MyBot(commands.Bot):
    async def setup_hook(self):
        print("Loading Cogs...")

        for filename in os.listdir("./Cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"Cogs.{filename[:-3]}")
                    print(f"Loaded: {filename}")
                except Exception as e:
                    print(f"Failed: {filename}")
                    print(e)

        # =====================
        # 💥完全安定同期
        # =====================

        # ① 開発サーバー即反映
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

        # ② 保険：グローバルも同期（本番用）
        await self.tree.sync()

        print("SYNC DONE (SAFE MODE)")


intents = discord.Intents.all()
bot = MyBot(command_prefix="$", intents=intents, help_command=None)


@bot.event
async def on_ready():
    print("起動成功👍")
    print("COGS:", list(bot.cogs.keys()))
    print("COMMANDS:", [c.name for c in bot.tree.get_commands()])


@bot.tree.error
async def on_app_command_error(interaction, error):
    print("ERROR:", error)
    try:
        await interaction.response.send_message(
            f"エラー: {error}",
            ephemeral=True
        )
    except:
        pass


bot.run(TOKEN)
