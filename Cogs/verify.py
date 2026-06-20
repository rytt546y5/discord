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
            label="問題の答えを入力してください",
            placeholder="数字を入力",
            required=True,
            max_length=3
        )

        self.add_item(self.user_answer)

    async def on_submit(self, interaction: discord.Interaction):

        member = interaction.guild.get_member(interaction.user.id)

        try:
            user_input = int(self.user_answer.value)
        except ValueError:
            return await interaction.response.send_message(
                "❌ 数字を入力してください。",
                ephemeral=True
            )

        # 既に付与済みチェック
        if self.role in member.roles:
            return await interaction.response.send_message(
                "✅ 既に認証済みです。",
                ephemeral=True
            )

        # 正解
        if user_input == self.answer:

            try:
                await member.add_roles(self.role, reason="認証成功")
            except discord.Forbidden:
                return await interaction.response.send_message(
                    "❌ Botにロール付与権限がありません。",
                    ephemeral=True
                )

            failed_attempts[member.id] = 0

            return await interaction.response.send_message(
                f"✅ 認証成功！\n{self.role.mention} を付与しました！",
                ephemeral=True
            )

        # 不正解
        failed_attempts[member.id] = failed_attempts.get(member.id, 0) + 1
        remain = 3 - failed_attempts[member.id]

        if failed_attempts[member.id] >= 3:

            try:
                await member.timeout(
                    timedelta(minutes=10),
                    reason="認証失敗3回"
                )
            except discord.Forbidden:
                pass

            failed_attempts[member.id] = 0

            return await interaction.response.send_message(
                "🚫 3回失敗したため10分タイムアウトしました。",
                ephemeral=True
            )

        return await interaction.response.send_message(
            f"❌ 不正解です。残り {remain} 回",
            ephemeral=True
        )


class VerifyButton(discord.ui.View):
    def __init__(self, role: discord.Role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(
        label="認証する",
        emoji="✅",
        style=discord.ButtonStyle.green
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        member = interaction.guild.get_member(interaction.user.id)

        if self.role in member.roles:
            return await interaction.response.send_message(
                "✅ 既に認証済みです。",
                ephemeral=True
            )

        num1 = random.randint(1, 9)
        num2 = random.randint(1, 9)

        if random.choice([True, False]):
            question = f"{num1} + {num2}"
            answer = num1 + num2
        else:
            if num2 > num1:
                num1, num2 = num2, num1
            question = f"{num1} - {num2}"
            answer = num1 - num2

        modal = VerifyModal(self.role, answer)
        modal.title = f"認証問題: {question}"

        await interaction.response.send_modal(modal)


class VerifyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="verify",
        description="認証パネルを作成します"
    )
    @app_commands.default_permissions(administrator=True)
    async def verify(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        role: discord.Role
    ):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.green()
        )

        view = VerifyButton(role)

        await interaction.channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            "✅ 認証パネルを作成しました。",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(VerifyCog(bot))
