import json
import os

import discord
from discord.ext import commands
from discord.ext.commands import Cog

from robocop_ng.helpers.checks import check_if_collaborator
from robocop_ng.helpers.invites import add_invite


class Invites(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.check(check_if_collaborator)
    async def invite(self, ctx):
        welcome_channel = self.bot.get_channel(self.bot.config.welcome_channel)
        author = ctx.message.author
        reason = f"Created by {str(author)} ({author.id})"
        invite = await welcome_channel.create_invite(
            max_age=0, max_uses=1, temporary=True, unique=True, reason=reason
        )

        add_invite(self.bot, invite.id, invite.url, 1, invite.code)

        await ctx.message.add_reaction("🆗")
        try:
            await ctx.author.send(f"Created single-use invite {invite.url}")
        except discord.errors.Forbidden:
            await ctx.send(
                f"{ctx.author.mention} I could not send you the \
                             invite. Send me a DM so I can reply to you."
            )


async def setup(bot):
    await bot.add_cog(Invites(bot))
