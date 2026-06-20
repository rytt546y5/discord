import discord
from discord import app_commands
from discord.ext import commands

class EmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="embed", description="埋め込みメッセージを送信します")
    @app_commands.describe(title="タイトル",description="本文",color="カラー",image="画像")
    @app_commands.choices(color=[
        app_commands.Choice(name="赤", value=0xE74C3C),
        app_commands.Choice(name="青", value=0x3498DB),
        app_commands.Choice(name="緑", value=0x2ECC71),
        app_commands.Choice(name="黄", value=0xF1C40F),
        app_commands.Choice(name="紫", value=0x9B59B6),
        app_commands.Choice(name="橙", value=0xE67E22),
        app_commands.Choice(name="白", value=0xFFFFFF),
        app_commands.Choice(name="黒", value=0x2F3136),
    ])
    @app_commands.default_permissions(administrator=True)
    async def embed(self,interaction: discord.Interaction,title: str,description: str,color: app_commands.Choice[int] = None,image: discord.Attachment = None):
        embed_color = color.value if color else 0x2F3136
        embed = discord.Embed(title=title, description=description, color=embed_color)
        if image:
            embed.set_image(url=image.url)

        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("送信しました!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(EmbedCog(bot))
