import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "gift_log.json"


# =====================
# DATA
# =====================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# =====================
# VIEW
# =====================

class GiftView(discord.ui.View):
    def __init__(self, product_name: str, log_channel_id: int):
        super().__init__(timeout=None)
        self.product_name = product_name
        self.log_channel_id = log_channel_id

    @discord.ui.button(
        label="🎁 受け取る",
        style=discord.ButtonStyle.green,
        custom_id="gift_receive"
    )
    async def receive(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = load_data()
        gid = str(interaction.message.id)

        # 初期化
        if gid not in data:
            data[gid] = []

        # 重複防止
        if interaction.user.id in data[gid]:
            return await interaction.response.send_message(
                "❌ すでに受け取り済みです",
                ephemeral=True
            )

        data[gid].append(interaction.user.id)
        save_data(data)

        # =====================
        # LOG CHANNEL FETCH
        # =====================

        try:
            log_channel = await interaction.guild.fetch_channel(self.log_channel_id)
        except:
            return await interaction.response.send_message(
                "❌ ログチャンネルが見つかりません",
                ephemeral=True
            )

        # =====================
        # EMBED
        # =====================

        embed = discord.Embed(
            title="🎁 配布ログ",
            color=discord.Color.gold()
        )

        embed.set_author(
            name=str(interaction.user),
            icon_url=interaction.user.display_avatar.url
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        embed.add_field(
            name="👤 受け取った人",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="📦 商品",
            value=self.product_name,
            inline=False
        )

        await log_channel.send(embed=embed)

        await interaction.response.send_message(
            "✅ 受け取り完了しました",
            ephemeral=True
        )


# =====================
# COG
# =====================

class Gift(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =====================
    # LOG SET
    # =====================

    @app_commands.command(
        name="gift_log_set",
        description="配布ログチャンネル設定"
    )
    async def log_set(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        data = load_data()
        data[str(interaction.guild.id)] = channel.id
        save_data(data)

        await interaction.response.send_message(
            "✅ 配布ログチャンネル設定完了",
            ephemeral=True
        )

    # =====================
    # PANEL SET
    # =====================

    @app_commands.command(
        name="gift_panel",
        description="配布パネル設置"
    )
    async def panel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        product_name: str,
        image: discord.Attachment = None
    ):

        data = load_data()
        log_id = data.get(str(interaction.guild.id))

        if not log_id:
            return await interaction.response.send_message(
                "❌ 先にログチャンネルを設定してください",
                ephemeral=True
            )

        embed = discord.Embed(
            title="🎁 配布パネル",
            description=f"商品: **{product_name}**",
            color=discord.Color.green()
        )

        if image:
            embed.set_image(url=image.url)

        embed.add_field(
            name="📌 受け取り方法",
            value="ボタンを押すだけで受け取れます",
            inline=False
        )

        await channel.send(
            embed=embed,
            view=GiftView(product_name, log_id)
        )

        await interaction.response.send_message(
            "✅ 配布パネル設置完了",
            ephemeral=True
        )


# =====================
# SETUP
# =====================

async def setup(bot):
    await bot.add_cog(Gift(bot))
