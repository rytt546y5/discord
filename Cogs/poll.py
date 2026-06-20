python
impod discord
from discord import app_commands
from discord.ext import commands

class PollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poll", description="投票を作成します")
    @app_commands.describe(title="タイトル",choice1="選択肢1", reaction1="リアクション1",choice2="選択肢2", reaction2="リアクション2",choice3="選択肢3", reaction3="リアクション3",choice4="選択肢4", reaction4="リアクション4",choice5="選択肢5", reaction5="リアクション5")
    async def poll(self,interaction: discord.Interaction,title: str,choice1: str, reaction1: str,choice2: str, reaction2: str,choice3: str = None, reaction3: str = None,choice4: str = None, reaction4: str = None,choice5: str = None, reaction5: str = None):
        options = [
            (choice1, reaction1),
            (choice2, reaction2),
        ]
        for choice, reaction in [(choice3, reaction3), (choice4, reaction4), (choice5, reaction5)]:
            if choice and reaction:
                options.append((choice, reaction))

        description = "\n".join(f"{reaction} {label}" for label, reaction in options)
        embed = discord.Embed(title=title, description=description, color=0xF1C40F)
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        for _, reaction in options:
            await message.add_reaction(reaction)

async def setup(bot):
    await bot.add_cog(PollCog(bot))
