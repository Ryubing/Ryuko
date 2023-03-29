from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import Cog, Context, BucketType

from robocop_ng.helpers.checks import check_if_staff
from robocop_ng.helpers.macros import get_macro, add_macro, edit_macro, remove_macro, get_macros


class Macro(Cog):
    @commands.cooldown(3, 30, BucketType.member)
    @commands.command(aliases=["m"])
    async def macro(self, ctx: Context, target: Optional[discord.Member], key: str):
        if len(key) > 0:
            text = get_macro(key)
            if text is not None:
                if target is not None:
                    await ctx.send(f"{target.mention}:\n{text}")
                else:
                    await ctx.send(text)
            else:
                await ctx.send(f"{ctx.author.mention}: The macro '{key}' doesn't exist.")

    @commands.check(check_if_staff)
    @commands.command(name="macroadd", aliases=["ma", "addmacro", "add_macro"])
    async def add_macro(self, ctx: Context, key: str, *, text: str):
        if add_macro(key, text):
            await ctx.send(f"Macro '{key}' added!")
        else:
            await ctx.send(f"Error: Macro '{key}' already exists.")

    @commands.check(check_if_staff)
    @commands.command(name="macroedit", aliases=["me", "editmacro", "edit_macro"])
    async def edit_macro(self, ctx: Context, key: str, *, text: str):
        if edit_macro(key, text):
            await ctx.send(f"Macro '{key}' edited!")
        else:
            await ctx.send(f"Error: Macro '{key}' not found.")

    @commands.check(check_if_staff)
    @commands.command(name="macroremove", aliases=[
        "mr", "md", "removemacro", "remove_macro", "macrodel", "delmacro", "delete_macro"
    ])
    async def remove_macro(self, ctx: Context, key: str):
        if remove_macro(key):
            await ctx.send(f"Macro '{key}' removed!")
        else:
            await ctx.send(f"Error: Macro '{key}' not found.")

    @commands.cooldown(3, 30, BucketType.channel)
    @commands.command(name="macros", aliases=["ml", "listmacros", "list_macros"])
    async def list_macros(self, ctx: Context):
        macros = get_macros()
        if len(macros) > 0:
            await ctx.send(
                "📝 **Macros**:\n"
                "\n".join([f"- {key}" for key in macros.keys()])
            )
        else:
            await ctx.send("Couldn't find any macros.")


async def setup(bot):
    await bot.add_cog(Macro(bot))
