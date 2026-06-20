@app_commands.command(name="giveaway", description="Giveaway作成（時間付き）")
@app_commands.default_permissions(administrator=True)
async def giveaway(
    self,
    interaction: discord.Interaction,
    title: str,
    prize: str,
    minutes: int = 0,
    winner_count: int = 1
):

    await interaction.response.defer(ephemeral=True)

    view = GiveawayView()

    embed = discord.Embed(
        title=f"🎉 {title}",
        description=(
            f"🎁 報酬: {prize}\n"
            f"👥 参加ボタンを押してください\n"
            f"⏰ 終了時間: {minutes if minutes > 0 else '未設定'}分"
        ),
        color=discord.Color.gold()
    )

    message = await interaction.channel.send(embed=embed, view=view)

    await interaction.followup.send("Giveaway作成完了", ephemeral=True)

    self.active_giveaway = {
        "message": message,
        "view": view,
        "winner_count": winner_count
    }

    if minutes > 0:
        await asyncio.sleep(minutes * 60)
        if self.active_giveaway:
            await self.end_giveaway(interaction.channel)
