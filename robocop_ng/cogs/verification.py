import asyncio
import hashlib
import itertools
import random
from inspect import cleandoc

import discord
from discord.ext import commands
from discord.ext.commands import Cog

from robocop_ng.helpers.checks import check_if_staff


class Verification(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hash_choice = random.choice(self.bot.config.welcome_hashes)

        # Export reset channel functions
        self.bot.do_reset = self.do_reset
        self.bot.do_resetalgo = self.do_resetalgo

    async def do_reset(self, channel, author, limit: int = 100):
        await channel.purge(limit=limit)

        await channel.send(self.bot.config.welcome_header)
        rules = [
            "**{}**. {}".format(i, cleandoc(r))
            for i, r in enumerate(self.bot.config.welcome_rules, 1)
        ]
        rule_choice = random.randint(2, len(rules))
        hash_choice_str = self.hash_choice.upper()
        if hash_choice_str == "BLAKE2B":
            hash_choice_str += "-512"
        elif hash_choice_str == "BLAKE2S":
            hash_choice_str += "-256"
        rules[rule_choice - 1] += "\n" + self.bot.config.hidden_term_line.format(
            hash_choice_str
        )
        msg = (
            f"🗑 **Reset**: {author} cleared {limit} messages " f" in {channel.mention}"
        )
        msg += f"\n💬 __Current challenge location__: under rule {rule_choice}"
        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        await log_channel.send(msg)

        # find rule that puts us over 2,000 characters, if any
        total = 0
        messages = []
        current_message = ""
        for item in rules:
            total += len(item) + 2  # \n\n
            if total < 2000:
                current_message += item + "\n\n"
            else:
                # we've hit the limit; split!
                messages += [current_message]
                current_message = "\n\u200b\n" + item + "\n\u200b\n"
                total = 0
        messages += [current_message]

        for item in messages:
            await channel.send(item)
            await asyncio.sleep(1)

        for x in self.bot.config.welcome_footer:
            await channel.send(cleandoc(x))
            await asyncio.sleep(1)

    async def do_resetalgo(self, channel, author, limit: int = 100):
        # randomize hash_choice on reset
        self.hash_choice = random.choice(tuple(self.bot.config.welcome_hashes))

        msg = (
            f"📘 **Reset Algorithm**: {author} reset " f"algorithm in {channel.mention}"
        )
        msg += f"\n💬 __Current algorithm__: {self.hash_choice.upper()}"
        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        await log_channel.send(msg)

        await self.do_reset(channel, author)

    @commands.check(check_if_staff)
    @commands.command()
    async def reset(self, ctx, limit: int = 100, force: bool = False):
        """Wipes messages and pastes the welcome message again. Staff only."""
        if ctx.message.channel.id != self.bot.config.welcome_channel and not force:
            await ctx.send(
                f"This command is limited to"
                f" <#{self.bot.config.welcome_channel}>, unless forced."
            )
            return
        await self.do_reset(ctx.channel, ctx.author.mention, limit)

    @commands.check(check_if_staff)
    @commands.command()
    async def resetalgo(self, ctx, limit: int = 100, force: bool = False):
        """Resets the verification algorithm and does what reset does. Staff only."""
        if ctx.message.channel.id != self.bot.config.welcome_channel and not force:
            await ctx.send(
                f"This command is limited to"
                f" <#{self.bot.config.welcome_channel}>, unless forced."
            )
            return

        await self.do_resetalgo(ctx.channel, ctx.author.mention, limit)

    async def process_message(self, message):
        """Big code that makes me want to shoot myself
        Not really a rewrite but more of a port

        Git blame tells me that I should blame/credit Robin Lambertz"""
        if message.channel.id == self.bot.config.welcome_channel:
            # Assign common stuff into variables to make stuff less of a mess
            member = message.author
            full_name = str(member)
            discrim = str(member.discriminator)
            guild = message.guild
            chan = message.channel
            mcl = message.content.lower()

            # Reply to users that insult the bot
            oof = [
                "bad",
                "broken",
                "buggy",
                "bugged",
                "stupid",
                "dumb",
                "silly",
                "fuck",
                "heck",
                "h*ck",
            ]
            if "bot" in mcl and any(insult in mcl for insult in oof):
                snark = random.choice(["bad human", "no u", "no u, rtfm", "pebkac"])
                return await chan.send(snark)

            # Get the role we will give in case of success
            success_role = guild.get_role(self.bot.config.named_roles["participant"])

            # Get a list of stuff we'll allow and will consider close
            allowed_names = [f"@{full_name}", full_name, str(member.id)]
            close_names = [f"@{member.name}", member.name, discrim, f"#{discrim}"]
            # Now add the same things but with newlines at the end of them
            allowed_names += [(an + "\n") for an in allowed_names]
            close_names += [(cn + "\n") for cn in close_names]
            allowed_names += [(an + "\r\n") for an in allowed_names]
            close_names += [(cn + "\r\n") for cn in close_names]
            # [ ͡° ͜ᔦ ͡°] 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝐌𝐚𝐜 𝐎𝐒 𝟗.
            allowed_names += [(an + "\r") for an in allowed_names]
            close_names += [(cn + "\r") for cn in close_names]

            # Finally, hash the stuff so that we can access them later :)
            hash_allow = [
                hashlib.new(self.hash_choice, name.encode("utf-8")).hexdigest()
                for name in allowed_names
            ]

            # I'm not even going to attempt to break those into lines jfc
            if any(allow in mcl for allow in hash_allow):
                await member.add_roles(success_role)
                return await chan.purge(
                    limit=100,
                    check=lambda m: m.author == message.author
                    or (
                        m.author == self.bot.user
                        and message.author.mention in m.content
                    ),
                )

            # Detect if the user uses the wrong hash algorithm
            wrong_hash_algos = list(
                set(self.bot.config.welcome_hashes) - {self.hash_choice}
            )
            for algo in wrong_hash_algos:
                for name in itertools.chain(allowed_names, close_names):
                    if hashlib.new(algo, name.encode("utf-8")).hexdigest() in mcl:
                        log_channel = self.bot.get_channel(self.bot.config.log_channel)
                        await log_channel.send(
                            f"User {message.author.mention} tried verification with algo {algo} instead of {self.hash_choice}."
                        )
                        return await chan.send(
                            f"{message.author.mention} :no_entry: Close, but not quite. Go back and re-read!"
                        )

            if (
                full_name in message.content
                or str(member.id) in message.content
                or member.name in message.content
                or discrim in message.content
            ):
                no_text = ":no_entry: Incorrect. You need to do something *specific* with your name and discriminator instead of just posting it. Please re-read the rules carefully and look up any terms you are not familiar with."
                rand_num = random.randint(1, 100)
                if rand_num == 42:
                    no_text = "you're doing it wrong"
                elif rand_num == 43:
                    no_text = "ugh, wrong, read the rules."
                elif rand_num == 44:
                    no_text = '"The definition of insanity is doing the same thing over and over again, but expecting different results."\n-Albert Einstein'
                await chan.send(f"{message.author.mention} {no_text}")

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


async def setup(bot):
    await bot.add_cog(Verification(bot))
