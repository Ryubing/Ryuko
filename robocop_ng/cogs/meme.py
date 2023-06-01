import datetime
import math
import platform
import random
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import Cog

from robocop_ng.helpers.checks import check_if_staff_or_ot


class Meme(Cog):
    """
    Meme commands.
    """

    def __init__(self, bot):
        self.bot = bot

    def c_to_f(self, c):
        """this is where we take memes too far"""
        return math.floor(9.0 / 5.0 * c + 32)

    def c_to_k(self, c):
        """this is where we take memes REALLY far"""
        return math.floor(c + 273.15)

    @commands.check(check_if_staff_or_ot)
    @commands.command(hidden=True, name="warm")
    async def warm_member(self, ctx, user: Optional[discord.Member]):
        """Warms a user :3"""
        if user is None and ctx.message.reference is None:
            celsius = random.randint(15, 20)
            fahrenheit = self.c_to_f(celsius)
            kelvin = self.c_to_k(celsius)
            await ctx.send(
                f"{ctx.author.mention} tries to warm themself."
                f" User is now {celsius}°C "
                f"({fahrenheit}°F, {kelvin}K).\n"
                "You might have more success warming someone else :3"
            )
        else:
            if user is None:
                user = (
                    await ctx.channel.fetch_message(ctx.message.reference.message_id)
                ).author

            celsius = random.randint(15, 100)
            fahrenheit = self.c_to_f(celsius)
            kelvin = self.c_to_k(celsius)
            await ctx.send(
                f"{user.mention} warmed."
                f" User is now {celsius}°C "
                f"({fahrenheit}°F, {kelvin}K)."
            )

    @commands.check(check_if_staff_or_ot)
    @commands.command(hidden=True)
    async def lick(self, ctx, user: Optional[discord.Member]):
        """licks a user :?"""
        if user is None and ctx.message.reference is None:
            await ctx.send(f"{ctx.author.mention} licks their lips! 👅")
        else:
            if user is None:
                user = (
                    await ctx.channel.fetch_message(ctx.message.reference.message_id)
                ).author
            await ctx.send(f"{user.mention} has been licked! 👅")

    @commands.check(check_if_staff_or_ot)
    @commands.command(hidden=True, name="chill", aliases=["cold"])
    async def chill_member(self, ctx, user: Optional[discord.Member]):
        """Chills a user >:3"""
        if user is None and ctx.message.reference is None:
            celsius = random.randint(-75, 10)
            fahrenheit = self.c_to_f(celsius)
            kelvin = self.c_to_k(celsius)
            await ctx.send(
                f"{ctx.author.mention} chills themself."
                f" User is now {celsius}°C "
                f"({fahrenheit}°F, {kelvin}K).\n"
                "🧊 Don't be so hard on yourself. 😔"
            )
        else:
            if user is None:
                user = (
                    await ctx.channel.fetch_message(ctx.message.reference.message_id)
                ).author
            celsius = random.randint(-50, 15)
            fahrenheit = self.c_to_f(celsius)
            kelvin = self.c_to_k(celsius)
            await ctx.send(
                f"{user.mention} chilled."
                f" User is now {celsius}°C "
                f"({fahrenheit}°F, {kelvin}K)."
            )

    @commands.check(check_if_staff_or_ot)
    @commands.command(hidden=True, aliases=["thank", "reswitchedgold"])
    async def gild(self, ctx, user: Optional[discord.Member]):
        """Gives a star to a user"""
        if user is None and ctx.message.reference is None:
            await ctx.send(f"No stars for you, {ctx.author.mention}!")
        else:
            if user is None:
                user = (
                    await ctx.channel.fetch_message(ctx.message.reference.message_id)
                ).author
            await ctx.send(f"{user.mention} gets a :star:, yay!")

    @commands.check(check_if_staff_or_ot)
    @commands.command(
        hidden=True, aliases=["reswitchedsilver", "silv3r", "reswitchedsilv3r"]
    )
    async def silver(self, ctx, user: Optional[discord.Member]):
        """Gives a user ReSwitched Silver™"""
        if user is None and ctx.message.reference is None:
            await ctx.send(f"{ctx.author.mention}, you can't reward yourself.")
        else:
            if user is None:
                user = (
                    await ctx.channel.fetch_message(ctx.message.reference.message_id)
                ).author
        embed = discord.Embed(
            title="ReSwitched Silver™!",
            description=f"Here's your ReSwitched Silver™," f"{user.mention}!",
        )
        embed.set_image(
            url="https://cdn.discordapp.com/emojis/548623626916724747.png?v=1"
        )
        await ctx.send(embed=embed)

    @commands.check(check_if_staff_or_ot)
    @commands.command(hidden=True)
    async def btwiuse(self, ctx):
        """btw i use arch"""
        uname = platform.uname()
        await ctx.send(
            f"BTW I use {platform.python_implementation()} "
            f"{platform.python_version()} on {uname.system} "
            f"{uname.release}"
        )

    @commands.check(check_if_staff_or_ot)
    @commands.command(hidden=True)
    async def yahaha(self, ctx):
        """secret command"""
        await ctx.send(f"🍂 you found me 🍂")

    @commands.check(check_if_staff_or_ot)
    @commands.command(hidden=True)
    async def blackalabi(self, ctx):
        """secret command"""
        await ctx.send("https://elixi.re/i/discord.png")

    @commands.check(check_if_staff_or_ot)
    @commands.command(hidden=True)
    async def peng(self, ctx):
        """heck tomger"""
        await ctx.send(f"🐧")

    @commands.check(check_if_staff_or_ot)
    @commands.command(hidden=True, aliases=["outstanding"])
    async def outstandingmove(self, ctx):
        """Posts the outstanding move meme"""
        await ctx.send(
            "https://cdn.discordapp.com/attachments"
            "/371047036348268545/528413677007929344"
            "/image0-5.jpg"
        )

    @commands.check(check_if_staff_or_ot)
    @commands.command(hidden=True)
    async def bones(self, ctx):
        await ctx.send("https://cdn.discordapp.com/emojis/443501365843591169.png?v=1")

    @commands.check(check_if_staff_or_ot)
    @commands.command(hidden=True)
    async def headpat(self, ctx):
        await ctx.send("https://cdn.discordapp.com/emojis/465650811909701642.png?v=1")

    @commands.check(check_if_staff_or_ot)
    @commands.command(
        hidden=True, aliases=["when", "etawhen", "emunand", "emummc", "thermosphere"]
    )
    async def eta(self, ctx):
        await ctx.send("June 15.")

    @commands.check(check_if_staff_or_ot)
    @commands.command(hidden=True, name="bam")
    async def bam_member(self, ctx, target: Optional[discord.Member]):
        """Bams a user owo"""
        if target is None and ctx.message.reference is None:
            await ctx.reply("https://tenor.com/view/bonk-gif-26414884")
        else:
            if target is None:
                target = (
                    await ctx.channel.fetch_message(ctx.message.reference.message_id)
                ).author
            if target == ctx.author:
                if target.id == 181627658520625152:
                    return await ctx.send(
                        "https://cdn.discordapp.com/attachments/286612533757083648/403080855402315796/rehedge.PNG"
                    )
                return await ctx.send("hedgeberg#7337 is ̶n͢ow b̕&̡.̷ 👍̡")
            elif target == self.bot.user:
                return await ctx.send(
                    f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
                )

            safe_name = await commands.clean_content(escape_markdown=True).convert(
                ctx, str(target)
            )
            await ctx.send(f"{safe_name} is ̶n͢ow b̕&̡.̷ 👍̡")

    @commands.command(hidden=True)
    async def memebercount(self, ctx):
        """Checks memeber count, as requested by dvdfreitag"""
        await ctx.send("There's like, uhhhhh a bunch")

    @commands.command(hidden=True)
    async def frolics(self, ctx):
        """test"""
        await ctx.send("https://www.youtube.com/watch?v=VmarNEsjpDI")

    @commands.command(
        hidden=True,
        aliases=[
            "yotld",
            "yold",
            "yoltd",
            "yearoflinuxondesktop",
            "yearoflinuxonthedesktop",
        ],
    )
    async def yearoflinux(self, ctx):
        """Shows the year of Linux on the desktop"""
        await ctx.send(
            f"{datetime.datetime.now().year} is the year of Linux on the Desktop"
        )


async def setup(bot):
    await bot.add_cog(Meme(bot))
