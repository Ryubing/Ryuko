import discord
from discord.ext import commands
from discord.ext.commands import Cog
import config
import random
from helpers.checks import check_if_staff


class RyujinxVerification(Cog):
    def __init__(self, bot):
        self.bot = bot

        # Export reset channel functions
        self.bot.do_reset = self.do_reset
        self.bot.do_resetalgo = self.do_resetalgo

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()

        if (member.guild.id not in config.guild_whitelist):
            return

        join_channel = self.bot.get_channel(config.welcome_channel)

        if join_channel is not None:
            await join_channel.send('Hello {0.mention}! Welcome to Ryujinx! Please read the <#411271165429022730>, and then type the verifying command here to gain access to the rest of the channels.\n\nIf you need help with basic common questions, visit the <#585288848704143371> channel after joining.\n\nIf you need help with Animal Crossing visit the <#692104087889641472> channel for common issues and solutions. If you need help that is not Animal Crossing related, please visit the <#410208610455519243> channel after verifying.'.format(member))

    async def process_message(self, message):
        """Process the verification process"""
        if message.channel.id == config.welcome_channel:
            # Assign common stuff into variables to make stuff less of a mess
            mcl = message.content.lower()

            # Get the role we will give in case of success
            success_role = message.guild.get_role(config.participant_role)

            if config.verification_string == mcl:
                await message.author.add_roles(success_role)
                await message.delete()

    @Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        try:
            await self.process_message(message)
        except discord.errors.Forbidden:
            chan = self.bot.get_channel(message.channel)
            await chan.send("💢 I don't have permission to do this.")

    @Cog.listener()
    async def on_message_edit(self, before, after):
        if after.author.bot:
            return

        try:
            await self.process_message(after)
        except discord.errors.Forbidden:
            chan = self.bot.get_channel(after.channel)
            await chan.send("💢 I don't have permission to do this.")

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()

        if (member.guild.id not in config.guild_whitelist):
            return

        join_channel = self.bot.get_channel(config.welcome_channel)

        if join_channel is not None:
            await join_channel.send(config.join_message.format(member))

    @commands.check(check_if_staff)
    @commands.command()
    async def reset(self, ctx, limit: int = 100, force: bool = False):
        """Wipes messages and pastes the welcome message again. Staff only."""
        if ctx.message.channel.id != config.welcome_channel and not force:
            await ctx.send(f"This command is limited to"
                           f" <#{config.welcome_channel}>, unless forced.")
            return
        await self.do_reset(ctx.channel, ctx.author.mention, limit)

    async def do_reset(self, channel, author, limit: int = 100):
        await channel.purge(limit=limit)

    async def do_resetalgo(self, channel, author, limit: int = 100):
        # We only auto clear the channel daily
        await self.do_reset(channel, author)

def setup(bot):
    bot.add_cog(RyujinxVerification(bot))
