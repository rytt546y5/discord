import discord
from discord.ext import commands
from discord import app_commands


def stars(n: int):
    return "⭐" * n + "☆" * (5 - n)


class AchievementModal(discord.ui.Modal):
    def __init__(self, log_channel: discord.TextChannel):
        super().__init__(title="実績記入")
        self.log_channel = log_channel

        self.title_input = discord.ui.TextInput(
            label="タイトル",
            max_length=50
        )

        self.content_input = discord.ui.TextInput(
            label="内容",
            style=discord.TextStyle.paragraph,
            max_length=300
        )

        self.rating_input = discord.ui.TextInput(
            label="評価（1〜5）",
            placeholder="例: 5",
            max_length=1
        )

        self.add_item(self.title_input)
        self.add_item(self.content_input)
        self.add_item(self.rating_input)

    async def on_submit(self, interaction: discord.Interaction):

        try:
            rating = int(self.rating_input.value)
            if rating < 1 or rating > 5:
                raise ValueError
        except:
            return await interaction.response.send_message(
                "❌ 評価は1〜5で入力してください",
                ephemeral=True
            )

        embed = discord.Embed(
            title="📊 実績報告",
            color=discord.Color.green()
        )

        embed.add_field(name="ユーザー", value=interaction.user.mention, inline=False)
        embed.add_field(name="タイトル", value=self.title_input.value, inline=False)
        embed.add_field(name="内容", value=self.content_input.value, inline=False)
        embed.add_field(name="評価", value=stars(rating), inline=False)

        await self.log_channel.send(embed=embed)

        await interaction.response.send_message(
            "✅ 実績を送信しました",
            ephemeral=True
        )


class AchievementView(discord.ui.View):
    def __init__(self, log_channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.log_channel = log_channel

    @discord.ui.button(label="実績を記入", style=discord.ButtonStyle.green, custom_id="achievement_btn")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AchievementModal(self.log_channel))


class Achievement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="実績記入パネル設置", description="実績パネルを設置します")
    @app_commands.default_permissions(administrator=True)
    async def panel(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        panel_channel: discord.TextChannel,
        log_channel: discord.TextChannel
    ):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )

        view = AchievementView(log_channel)

        await panel_channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            "✅ 実績パネルを設置しました",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Achievement(bot))
