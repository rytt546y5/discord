import discord
from discord.ext import commands
from discord import app_commands
import random
from datetime import timedelta

failed_attempts = {}


class VerifyModal(discord.ui.Modal):
    def __init__(self, role: discord.Role, answer: int):
        super().__init__(title="認証")
        self.role = role
        self.answer = answer

        self.user_answer = discord.ui.TextInput(
            label="答えを入力",
            placeholder="数字",
            required=True,
            max_length=3
        )

        self.add_item(self.user_answer)

    async def on_submit(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        member = interaction.guild.get_member(interaction.user.id)

        try:
            user_input = int(self.user_answer.value)
        except:
            return await interaction.followup.send("❌ 数字を入力してください", ephemeral=True)

        if self.role in member.roles:
            return await interaction.followup.send("✅ 既に認証済みです", ephemeral=True)

        if user_input == self.answer:

            try:
                await member.add_roles(self.role, reason="認証成功")
            except discord.Forbidden:
                return await interaction.followup.send("❌ 権限不足", ephemeral=True)

            failed_attempts[member.id] = 0

            return await interaction.followup.send(
                f"✅ 認証成功！ {self.role.mention}付与",
                ephemeral=True
            )

        failed_attempts[member.id] = failed_attempts.get(member.id, 0) + 1
        remain = 3 - failed_attempts[member.id]

        if failed_attempts[member.id] >= 3:

            try:
                await member.timeout(timedelta(minutes=10), reason="認証失敗")
            except:
                pass

            failed_attempts[member.id] = 0

            return await interaction.followup.send(
                "🚫 3回失敗で10分タイムアウト",
                ephemeral=True
            )

        await interaction.followup.send(
            f"❌ 不正解 残り{remain}",
            ephemeral=True
        )


class VerifyView(discord.ui.View):
    def __init__(self, role: discord.Role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(label="認証する", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        member = interaction.guild.get_member(interaction.user.id)

        if self.role in member.roles:
            return await interaction.response.send_message("既に認証済み", ephemeral=True)

        n1 = random.randint(1, 9)
        n2 = random.randint(1, 9)

        if random.choice([True, False]):
            question = f"{n1} + {n2}"
            answer = n1 + n2
        else:
            if n2 > n1:
                n1, n2 = n2, n1
            question = f"{n1} - {n2}"
            answer = n1 - n2

        modal = VerifyModal(self.role, answer)
        modal.title = f"認証問題: {question}"

        await interaction.response.send_modal(modal)


class VerifyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="verify", description="認証パネル設置")
    async def verify_panel(self, interaction: discord.Interaction, title: str, description: str, role: discord.Role):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.green()
        )

        view = VerifyView(role)

        await interaction.channel.send(embed=embed, view=view)

        await interaction.response.send_message("✅ 設置完了", ephemeral=True)


async def setup(bot):
    await bot.add_cog(VerifyCog(bot))
