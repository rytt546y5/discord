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
            max_length=2
        )
        self.add_item(self.user_answer)
    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        try:
            user_input = int(self.user_answer.value)
        except ValueError:
            await interaction.response.send_message(
                "❌ 数字を入力してください。",
                ephemeral=True
            )
            return
        if user_input == self.answer:
            if self.role in interaction.user.roles:
                await interaction.response.send_message(
                    "✅ 既に認証済みです。",
                    ephemeral=True
                )
                return
            await interaction.user.add_roles(
                self.role,
                reason="認証成功"
            )
            failed_attempts[user_id] = 0
            await interaction.response.send_message(
                f"✅ 認証成功！\n{self.role.mention} が付与されました！",
                ephemeral=True
            )
        else:
            failed_attempts[user_id] = failed_attempts.get(user_id, 0) + 1
            remain = 3 - failed_attempts[user_id]
            if failed_attempts[user_id] >= 3:
                try:
                    await interaction.user.timeout(
                        timedelta(minutes=10),
                        reason="認証3回失敗"
                    )
                except Exception:
                    pass
                failed_attempts[user_id] = 0
                await interaction.response.send_message(
                    "🚫 認証に3回失敗したため10分間タイムアウトされました。",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ 不正解です。\n残り {remain} 回です。",
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
    async def verify(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.role in interaction.user.roles:
            await interaction.response.send_message(
                "✅ 既に認証済みです。",
                ephemeral=True
            )
            return
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
        await interaction.channel.send(
            embed=embed,
            view=view
        )
        await interaction.response.send_message(
            "✅ 認証パネルを作成しました。",
            ephemeral=True
        )
async def setup(bot):
    await bot.add_cog(VerifyCog(bot))
