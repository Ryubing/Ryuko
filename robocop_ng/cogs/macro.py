from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import Cog, Context, BucketType

from robocop_ng.helpers.checks import check_if_staff
from robocop_ng.helpers.macros import (
    get_macro,
    add_macro,
    edit_macro,
    remove_macro,
    get_macros_dict,
    add_aliases,
    remove_aliases,
    clear_aliases,
)


class Macro(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(3, 30, BucketType.member)
    @commands.command(aliases=["m"])
    async def macro(
        self, ctx: Context, key: str, target: Optional[discord.Member] = None
    ):
        await ctx.message.delete()
        if len(key) > 0:
            text = get_macro(self.bot, key)
            if text is not None:
                if target is not None:
                    await ctx.send(f"{target.mention}:\n{text}")
                else:
                    if ctx.message.reference is not None:
                        await ctx.send(
                            text, reference=ctx.message.reference, mention_author=True
                        )
                    else:
                        await ctx.send(text)
            else:
                await ctx.send(
                    f"{ctx.author.mention}: The macro '{key}' doesn't exist."
                )

    @commands.check(check_if_staff)
    @commands.command(name="macroadd", aliases=["ma", "addmacro", "add_macro"])
    async def add_macro(self, ctx: Context, key: str, *, text: str):
        if add_macro(self.bot, key, text):
            await ctx.send(f"Macro '{key}' added!")
        else:
            await ctx.send(f"Error: Macro '{key}' already exists.")

    @commands.check(check_if_staff)
    @commands.command(name="aliasadd", aliases=["addalias", "add_alias"])
    async def add_alias_macro(self, ctx: Context, existing_key: str, *new_keys: str):
        if len(new_keys) == 0:
            await ctx.send("Error: You need to add at least one alias.")
        else:
            if add_aliases(self.bot, existing_key, list(new_keys)):
                await ctx.send(
                    f"Added {len(new_keys)} aliases to macro '{existing_key}'!"
                )
            else:
                await ctx.send(f"Error: No new and unique aliases found.")

    @commands.check(check_if_staff)
    @commands.command(name="macroedit", aliases=["me", "editmacro", "edit_macro"])
    async def edit_macro(self, ctx: Context, key: str, *, text: str):
        if edit_macro(self.bot, key, text):
            await ctx.send(f"Macro '{key}' edited!")
        else:
            await ctx.send(f"Error: Macro '{key}' not found.")

    @commands.check(check_if_staff)
    @commands.command(
        name="aliasremove",
        aliases=[
            "aliasdelete",
            "delalias",
            "aliasdel",
            "removealias",
            "remove_alias",
            "delete_alias",
        ],
    )
    async def remove_alias_macro(
        self, ctx: Context, existing_key: str, *remove_keys: str
    ):
        if len(remove_keys) == 0:
            await ctx.send("Error: You need to remove at least one alias.")
        else:
            if remove_aliases(self.bot, existing_key, list(remove_keys)):
                await ctx.send(
                    f"Removed {len(remove_keys)} aliases from macro '{existing_key}'!"
                )
            else:
                await ctx.send(
                    f"Error: None of the specified aliases were found for macro '{existing_key}'."
                )

    @commands.check(check_if_staff)
    @commands.command(
        name="macroremove",
        aliases=[
            "mr",
            "md",
            "removemacro",
            "remove_macro",
            "macrodel",
            "delmacro",
            "delete_macro",
        ],
    )
    async def remove_macro(self, ctx: Context, key: str):
        if remove_macro(self.bot, key):
            await ctx.send(f"Macro '{key}' removed!")
        else:
            await ctx.send(f"Error: Macro '{key}' not found.")

    @commands.check(check_if_staff)
    @commands.command(name="aliasclear", aliases=["clearalias", "clear_alias"])
    async def clear_alias_macro(self, ctx: Context, existing_key: str):
        if clear_aliases(self.bot, existing_key):
            await ctx.send(f"Removed all aliases of macro '{existing_key}'!")
        else:
            await ctx.send(f"Error: No aliases found for macro '{existing_key}'.")

    @commands.cooldown(3, 30, BucketType.channel)
    @commands.command(name="macros", aliases=["ml", "listmacros", "list_macros"])
    async def list_macros(self, ctx: Context, macros_only=False):
        macros = get_macros_dict(self.bot)
        if len(macros["macros"]) > 0:
            messages = []
            num_messages = (
                len(macros["macros"]) // 50 if len(macros["macros"]) > 50 else 1
            )
            message = ""

            for index, key in zip(
                range(len(macros["macros"])), sorted(macros["macros"].keys())
            ):
                if index == 0 or index + 1 % 50 == 0:
                    if len(message) > 0:
                        messages.append(message)
                    message = f"📝 **Macros** ({len(messages) + 1}/{num_messages}):\n"
                message += f"- {key}\n"
                if not macros_only and key in macros["aliases"].keys():
                    message += "  - __aliases__: "
                    first_alias = True
                    for alias in macros["aliases"][key]:
                        if first_alias:
                            message += alias
                            first_alias = False
                            continue
                        message += f", {alias}"
                    message += "\n"

            # Add the last message as well
            messages.append(message)

            for msg in messages:
                await ctx.send(msg)
        else:
            await ctx.send("Couldn't find any macros.")

    @commands.cooldown(3, 30, BucketType.channel)
    @commands.command(name="aliases", aliases=["listaliases", "list_aliases"])
    async def list_aliases(self, ctx: Context, existing_key: str):
        macros = get_macros_dict(self.bot)
        existing_key = existing_key.lower()
        if existing_key in macros["aliases"].keys():
            message = f"📝 **Aliases for '{existing_key}'**:\n"
            for alias in sorted(macros["aliases"][existing_key]):
                message += f"- {alias}\n"
            await ctx.send(message)
        else:
            await ctx.send(f"Couldn't find any aliases for macro '{existing_key}'.")


async def setup(bot):
    await bot.add_cog(Macro(bot))
