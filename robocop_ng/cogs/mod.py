import io
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import Cog

from robocop_ng.helpers.checks import check_if_staff, check_if_bot_manager
from robocop_ng.helpers.restrictions import add_restriction, remove_restriction
from robocop_ng.helpers.userlogs import userlog


class Mod(Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_if_target_is_staff(self, target):
        return any(r.id in self.bot.config.staff_role_ids for r in target.roles)

    @commands.guild_only()
    @commands.check(check_if_bot_manager)
    @commands.command()
    async def setguildicon(self, ctx, url):
        """Changes guild icon, bot manager only."""
        img_bytes = await self.bot.aiogetbytes(url)
        await ctx.guild.edit(icon=img_bytes, reason=str(ctx.author))
        await ctx.send(f"Done!")

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        log_msg = (
            f"✏️ **Guild Icon Update**: {ctx.author} changed the guild icon."
            f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
        )
        img_filename = url.split("/")[-1].split("#")[0]  # hacky
        img_file = discord.File(io.BytesIO(img_bytes), filename=img_filename)
        await log_channel.send(log_msg, file=img_file)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def mute(self, ctx, target: Optional[discord.Member], *, reason: str = ""):
        """Mutes a user, staff only."""
        if target is None and ctx.message.reference is None:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        else:
            if ctx.message.reference is not None:
                if target is not None:
                    reason = str(target) + reason
                target = (
                    await ctx.channel.fetch_message(ctx.message.reference.message_id)
                ).author
        # Hedge-proofing the code
        if target == ctx.author:
            return await ctx.send("You can't do mod actions on yourself.")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send(
                "I can't mute this user as they're a member of staff."
            )

        userlog(self.bot, target.id, ctx.author, reason, "mutes", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        dm_message = f"You were muted!"
        if reason:
            dm_message += f' The given reason is: "{reason}".'

        try:
            await target.send(dm_message)
        except discord.errors.Forbidden:
            # Prevents kick issues in cases where user blocked bot
            # or has DMs disabled
            pass

        mute_role = ctx.guild.get_role(self.bot.config.mute_role)

        await target.add_roles(mute_role, reason=str(ctx.author))

        chan_message = (
            f"🔇 **Muted**: {str(ctx.author)} muted "
            f"{target.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target.id}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future, "
                "it is recommended to use `.mute <user> [reason]`"
                " as the reason is automatically sent to the user."
            )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        await log_channel.send(chan_message)
        await ctx.send(f"{target.mention} can no longer speak.")
        add_restriction(self.bot, target.id, self.bot.config.mute_role)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def unmute(self, ctx, target: discord.Member):
        """Unmutes a user, staff only."""
        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        mute_role = ctx.guild.get_role(self.bot.config.mute_role)
        await target.remove_roles(mute_role, reason=str(ctx.author))

        chan_message = (
            f"🔈 **Unmuted**: {str(ctx.author)} unmuted "
            f"{target.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target.id}\n"
        )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        await log_channel.send(chan_message)
        await ctx.send(f"{target.mention} can now speak again.")
        remove_restriction(self.bot, target.id, self.bot.config.mute_role)

    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def kick(self, ctx, target: Optional[discord.Member], *, reason: str = ""):
        """Kicks a user, staff only."""
        if target is None and ctx.message.reference is None:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        else:
            if ctx.message.reference is not None:
                if target is not None:
                    reason = str(target) + reason
                target = (
                    await ctx.channel.fetch_message(ctx.message.reference.message_id)
                ).author
        # Hedge-proofing the code
        if target == ctx.author:
            return await ctx.send("You can't do mod actions on yourself.")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send(
                "I can't kick this user as they're a member of staff."
            )

        userlog(self.bot, target.id, ctx.author, reason, "kicks", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        dm_message = f"You were kicked from {ctx.guild.name}."
        if reason:
            dm_message += f' The given reason is: "{reason}".'
        dm_message += (
            "\n\nYou are able to rejoin the server,"
            " but please be sure to behave when participating again."
        )

        try:
            await target.send(dm_message)
        except discord.errors.Forbidden:
            # Prevents kick issues in cases where user blocked bot
            # or has DMs disabled
            pass

        await target.kick(reason=f"{ctx.author}, reason: {reason}")
        chan_message = (
            f"👢 **Kick**: {str(ctx.author)} kicked "
            f"{target.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target.id}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future"
                ", it is recommended to use "
                "`.kick <user> [reason]`"
                " as the reason is automatically sent to the user."
            )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        await log_channel.send(chan_message)
        await ctx.send(f"👢 {safe_name}, 👍.")

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["yeet"])
    async def ban(self, ctx, target: Optional[discord.Member], *, reason: str = ""):
        """Bans a user, staff only."""
        if target is None and ctx.message.reference is None:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        else:
            if ctx.message.reference is not None:
                if target is not None:
                    reason = str(target) + reason
                target = (
                    await ctx.channel.fetch_message(ctx.message.reference.message_id)
                ).author
        # Hedge-proofing the code
        if target == ctx.author:
            if target.id == 181627658520625152:
                return await ctx.send(
                    "https://cdn.discordapp.com/attachments/286612533757083648/403080855402315796/rehedge.PNG"
                )
            return await ctx.send("hedgeberg#7337 is now b&. 👍")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I can't ban this user as they're a member of staff.")

        userlog(self.bot, target.id, ctx.author, reason, "bans", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        dm_message = f"You were banned from {ctx.guild.name}."
        if reason:
            dm_message += f' The given reason is: "{reason}".'
        dm_message += "\n\nThis ban does not expire."

        try:
            await target.send(dm_message)
        except discord.errors.Forbidden:
            # Prevents ban issues in cases where user blocked bot
            # or has DMs disabled
            pass

        await target.ban(
            reason=f"{ctx.author}, reason: {reason}", delete_message_days=0
        )
        chan_message = (
            f"⛔ **Ban**: {str(ctx.author)} banned "
            f"{target.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target.id}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future"
                ", it is recommended to use `.ban <user> [reason]`"
                " as the reason is automatically sent to the user."
            )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        await log_channel.send(chan_message)
        await ctx.send(f"{safe_name} is now b&. 👍")

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def bandel(
        self, ctx, day_count: int, target: Optional[discord.Member], *, reason: str = ""
    ):
        """Bans a user for a given number of days, staff only."""
        if target is None and ctx.message.reference is None:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        else:
            if ctx.message.reference is not None:
                if target is not None:
                    reason = str(target) + reason
                target = (
                    await ctx.channel.fetch_message(ctx.message.reference.message_id)
                ).author
        # Hedge-proofing the code
        if target == ctx.author:
            if target.id == 181627658520625152:
                return await ctx.send(
                    "https://cdn.discordapp.com/attachments/286612533757083648/403080855402315796/rehedge.PNG"
                )
            return await ctx.send("hedgeberg#7337 is now b&. 👍")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I can't ban this user as they're a member of staff.")

        if day_count < 0 or day_count > 7:
            return await ctx.send(
                "Message delete day count needs to be between 0 and 7 days."
            )

        userlog(self.bot, target.id, ctx.author, reason, "bans", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        dm_message = f"You were banned from {ctx.guild.name}."
        if reason:
            dm_message += f' The given reason is: "{reason}".'
        dm_message += "\n\nThis ban does not expire."

        try:
            await target.send(dm_message)
        except discord.errors.Forbidden:
            # Prevents ban issues in cases where user blocked bot
            # or has DMs disabled
            pass

        await target.ban(
            reason=f"{ctx.author}, days of message deletions: {day_count}, reason: {reason}",
            delete_message_days=day_count,
        )
        chan_message = (
            f"⛔ **Ban**: {str(ctx.author)} banned with {day_count} of messages deleted "
            f"{target.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target.id}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future"
                ", it is recommended to use `.bandel <daycount> <user> [reason]`"
                " as the reason is automatically sent to the user."
            )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        await log_channel.send(chan_message)
        await ctx.send(
            f"{safe_name} is now b&, with {day_count} days of messages deleted. 👍"
        )

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["softban"])
    async def hackban(self, ctx, target: int, *, reason: str = ""):
        """Bans a user with their ID, doesn't message them, staff only."""
        target_user = await self.bot.fetch_user(target)
        target_member = ctx.guild.get_member(target)
        # Hedge-proofing the code
        if target == ctx.author.id:
            return await ctx.send("You can't do mod actions on yourself.")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif target_member and self.check_if_target_is_staff(target_member):
            return await ctx.send("I can't ban this user as they're a member of staff.")

        userlog(self.bot, target, ctx.author, reason, "bans", target_user.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        await ctx.guild.ban(
            target_user, reason=f"{ctx.author}, reason: {reason}", delete_message_days=0
        )
        chan_message = (
            f"⛔ **Hackban**: {str(ctx.author)} banned "
            f"{target_user.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future"
                ", it is recommended to use "
                "`.hackban <user> [reason]`."
            )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        await log_channel.send(chan_message)
        await ctx.send(f"{safe_name} is now b&. 👍")

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def massban(self, ctx, *, targets: str):
        """Bans users with their IDs, doesn't message them, staff only."""
        targets_int = [int(target) for target in targets.strip().split(" ")]
        for target in targets_int:
            target_user = await self.bot.fetch_user(target)
            target_member = ctx.guild.get_member(target)
            # Hedge-proofing the code
            if target == ctx.author.id:
                await ctx.send(f"(re: {target}) You can't do mod actions on yourself.")
                continue
            elif target == self.bot.user:
                await ctx.send(
                    f"(re: {target}) I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
                )
                continue
            elif target_member and self.check_if_target_is_staff(target_member):
                await ctx.send(
                    f"(re: {target}) I can't ban this user as they're a member of staff."
                )
                continue

            userlog(self.bot, target, ctx.author, f"massban", "bans", target_user.name)

            safe_name = await commands.clean_content(escape_markdown=True).convert(
                ctx, str(target)
            )

            await ctx.guild.ban(
                target_user,
                reason=f"{ctx.author}, reason: massban",
                delete_message_days=0,
            )
            chan_message = (
                f"⛔ **Massban**: {str(ctx.author)} banned "
                f"{target_user.mention} | {safe_name}\n"
                f"🏷 __User ID__: {target}\n"
                "Please add an explanation below."
            )

            chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

            log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
            await log_channel.send(chan_message)
        await ctx.send(f"All {len(targets_int)} users are now b&. 👍")

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def unban(self, ctx, target: int, *, reason: str = ""):
        """Unbans a user with their ID, doesn't message them, staff only."""
        target_user = await self.bot.fetch_user(target)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        await ctx.guild.unban(target_user, reason=f"{ctx.author}, reason: {reason}")
        chan_message = (
            f"⚠️ **Unban**: {str(ctx.author)} unbanned "
            f"{target_user.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future"
                ", it is recommended to use "
                "`.unban <user id> [reason]`."
            )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        await log_channel.send(chan_message)
        await ctx.send(f"{safe_name} is now unb&.")

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def silentban(self, ctx, target: discord.Member, *, reason: str = ""):
        """Bans a user, staff only."""
        # Hedge-proofing the code
        if target == ctx.author:
            return await ctx.send("You can't do mod actions on yourself.")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I can't ban this user as they're a member of staff.")

        userlog(self.bot, target.id, ctx.author, reason, "bans", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        await target.ban(
            reason=f"{ctx.author}, reason: {reason}", delete_message_days=0
        )
        chan_message = (
            f"⛔ **Silent ban**: {str(ctx.author)} banned "
            f"{target.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target.id}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future"
                ", it is recommended to use `.ban <user> [reason]`"
                " as the reason is automatically sent to the user."
            )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        await log_channel.send(chan_message)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def approve(
        self, ctx, target: Optional[discord.Member], role: str = "community"
    ):
        """Add a role to a user (default: community), staff only."""
        if role not in self.bot.config.named_roles:
            return await ctx.send(
                "No such role! Available roles: "
                + ",".join(self.bot.config.named_roles)
            )

        if target is None and ctx.message.reference is None:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        else:
            if ctx.message.reference is not None:
                target = (
                    await ctx.channel.fetch_message(ctx.message.reference.message_id)
                ).author

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        target_role = ctx.guild.get_role(self.bot.config.named_roles[role])

        if target_role in target.roles:
            return await ctx.send("Target already has this role.")

        await target.add_roles(target_role, reason=str(ctx.author))

        await ctx.send(f"Approved {target.mention} to `{role}` role.")

        await log_channel.send(
            f"✅ Approved: {str(ctx.author)} added"
            f" {role} to {target.mention}"
            f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
        )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["unapprove"])
    async def revoke(
        self, ctx, target: Optional[discord.Member], role: str = "community"
    ):
        """Remove a role from a user (default: community), staff only."""
        if role not in self.bot.config.named_roles:
            return await ctx.send(
                "No such role! Available roles: "
                + ",".join(self.bot.config.named_roles)
            )

        if target is None and ctx.message.reference is None:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        else:
            if ctx.message.reference is not None:
                target = (
                    await ctx.channel.fetch_message(ctx.message.reference.message_id)
                ).author

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        target_role = ctx.guild.get_role(self.bot.config.named_roles[role])

        if target_role not in target.roles:
            return await ctx.send("Target doesn't have this role.")

        await target.remove_roles(target_role, reason=str(ctx.author))

        await ctx.send(f"Un-approved {target.mention} from `{role}` role.")

        await log_channel.send(
            f"❌ Un-approved: {str(ctx.author)} removed"
            f" {role} from {target.mention}"
            f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
        )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["clear"])
    async def purge(self, ctx, limit: int, channel: discord.TextChannel = None):
        """Clears a given number of messages, staff only."""
        modlog_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        if not channel:
            channel = ctx.channel

        purged_log_jump_url = ""
        for deleted_message in await channel.purge(limit=limit):
            msg = (
                "🗑️ **Message purged**: \n"
                f"from {self.bot.escape_message(deleted_message.author.name)} "
                f"({deleted_message.author.id}), in {deleted_message.channel.mention}:\n"
                f"`{deleted_message.clean_content}`"
            )
            if len(purged_log_jump_url) == 0:
                purged_log_jump_url = (await log_channel.send(msg)).jump_url
            else:
                await log_channel.send(msg)

        msg = (
            f"🗑 **Purged**: {str(ctx.author)} purged {limit} "
            f"messages in {channel.mention}."
            f"\n🔗 __Jump__: <{purged_log_jump_url}>"
        )
        await modlog_channel.send(msg)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def warn(self, ctx, target: Optional[discord.Member], *, reason: str = ""):
        """Warns a user, staff only."""
        if target is None and ctx.message.reference is None:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        else:
            if ctx.message.reference is not None:
                if target is not None:
                    reason = str(target) + reason
                target = (
                    await ctx.channel.fetch_message(ctx.message.reference.message_id)
                ).author
        # Hedge-proofing the code
        if target == ctx.author:
            return await ctx.send("You can't do mod actions on yourself.")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send(
                "I can't warn this user as they're a member of staff."
            )

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        warn_count = userlog(
            self.bot, target.id, ctx.author, reason, "warns", target.name
        )

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )
        chan_msg = (
            f"⚠️ **Warned**: {str(ctx.author)} warned "
            f"{target.mention} (warn #{warn_count}) "
            f"| {safe_name}\n"
        )

        msg = f"You were warned on {ctx.guild.name}."
        if reason:
            msg += " The given reason is: " + reason
        msg += (
            f"\n\nPlease read the rules in {self.bot.config.rules_url}. "
            f"This is warn #{warn_count}."
        )
        if warn_count == 2:
            msg += " __The next warn will automatically kick.__"
        if warn_count == 3:
            msg += (
                "\n\nYou were kicked because of this warning. "
                "This is your final warning. "
                "You can join again, but "
                "**one more warn will result in a ban**."
            )
            chan_msg += "**This resulted in an auto-kick.**\n"
        if warn_count == 4:
            msg += "\n\nYou were automatically banned due to four warnings."
            chan_msg += "**This resulted in an auto-ban.**\n"
        try:
            await target.send(msg)
        except discord.errors.Forbidden:
            # Prevents log issues in cases where user blocked bot
            # or has DMs disabled
            pass
        if warn_count == 3:
            await target.kick()
        if warn_count >= 4:  # just in case
            await target.ban(reason="exceeded warn limit", delete_message_days=0)
        await ctx.send(
            f"{target.mention} warned. " f"User has {warn_count} warning(s)."
        )

        if reason:
            chan_msg += f'✏️ __Reason__: "{reason}"'
        else:
            chan_msg += (
                "Please add an explanation below. In the future"
                ", it is recommended to use `.warn <user> [reason]`"
                " as the reason is automatically sent to the user."
            )

        chan_msg += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        await log_channel.send(chan_msg)

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["softwarn"])
    async def hackwarn(self, ctx, target: int, *, reason: str = ""):
        """Warns a user with their ID, doesn't message them, staff only."""
        target_user = await self.bot.fetch_user(target)
        target_member = ctx.guild.get_member(target)
        # Hedge-proofing the code
        if target == ctx.author.id:
            return await ctx.send("You can't do mod actions on yourself.")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif target_member and self.check_if_target_is_staff(target_member):
            return await ctx.send(
                "I can't warn this user as they're a member of staff."
            )

        warn_count = userlog(
            self.bot, target, ctx.author, reason, "warns", target_user.name
        )

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        chan_msg = (
            f"⚠️ **Hackwarned**: {str(ctx.author)} warned "
            f"{target_user.mention} (warn #{warn_count}) | {safe_name}\n"
            f"🏷 __User ID__: {target}\n"
        )

        if warn_count == 4:
            userlog(
                self.bot,
                target,
                ctx.author,
                "exceeded warn limit",
                "bans",
                target_user.name,
            )
            chan_msg += "**This resulted in an auto-hackban.**\n"
            await ctx.guild.ban(
                target_user,
                reason=f"{ctx.author}, reason: exceeded warn limit",
                delete_message_days=0,
            )

        if reason:
            chan_msg += f'✏️ __Reason__: "{reason}"'
        else:
            chan_msg += (
                "Please add an explanation below. In the future"
                ", it is recommended to use "
                "`.hackwarn <user> [reason]`."
            )

        chan_msg += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        await log_channel.send(chan_msg)
        await ctx.send(f"{safe_name} warned. " f"User has {warn_count} warning(s).")

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["setnick", "nick"])
    async def nickname(self, ctx, target: Optional[discord.Member], *, nick: str = ""):
        """Sets a user's nickname, staff only.

        Just send .nickname <user> to wipe the nickname."""
        if target is None and ctx.message.reference is None:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        else:
            if ctx.message.reference is not None:
                target = (
                    await ctx.channel.fetch_message(ctx.message.reference.message_id)
                ).author

        try:
            if nick:
                await target.edit(nick=nick, reason=str(ctx.author))
            else:
                await target.edit(nick=None, reason=str(ctx.author))

            await ctx.send("Successfully set nickname.")
        except discord.errors.Forbidden:
            await ctx.send(
                "I don't have the permission to set that user's nickname.\n"
                "User's top role may be above mine, or I may lack Manage Nicknames permission."
            )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["echo"])
    async def say(self, ctx, *, the_text: str):
        """Repeats a given text, staff only."""
        await ctx.send(the_text)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def speak(self, ctx, channel: discord.TextChannel, *, the_text: str):
        """Repeats a given text in a given channel, staff only."""
        await channel.send(the_text)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["setplaying", "setgame"])
    async def playing(self, ctx, *, game: str = ""):
        """Sets the bot's currently played game name, staff only.

        Just send .playing to wipe the playing state."""
        if game:
            await self.bot.change_presence(activity=discord.Game(name=game))
        else:
            await self.bot.change_presence(activity=None)

        await ctx.send("Successfully set game.")

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["setbotnick", "botnick", "robotnick"])
    async def botnickname(self, ctx, *, nick: str = ""):
        """Sets the bot's nickname, staff only.

        Just send .botnickname to wipe the nickname."""

        if nick:
            await ctx.guild.me.edit(nick=nick, reason=str(ctx.author))
        else:
            await ctx.guild.me.edit(nick=None, reason=str(ctx.author))

        await ctx.send("Successfully set bot nickname.")

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def move(self, ctx, channelTo: discord.TextChannel, *, limit: int):
        """Move a user to another channel, staff only.

        !move {channel to move to} {number of messages}"""
        # get a list of the messages
        fetchedMessages = []

        async for message in ctx.channel.history(limit=limit + 1):
            fetchedMessages.append(message)

        # delete all of those messages from the channel
        for i in fetchedMessages:
            await i.delete()

        # invert the list and remove the last message (gets rid of the command message)
        fetchedMessages = fetchedMessages[::-1]
        fetchedMessages = fetchedMessages[:-1]

        # Loop over the messages fetched
        for message in fetchedMessages:
            # if the message is embedded already
            if message.embeds:
                # set the embed message to the old embed object
                embedMessage = message.embeds[0]
            # else
            else:
                # Create embed message object and set content to original
                embedMessage = discord.Embed(description=message.content)

                avatar_url = None

                if message.author.display_avatar is not None:
                    avatar_url = str(message.author.display_avatar)

                # set the embed message author to original author
                embedMessage.set_author(name=message.author, icon_url=avatar_url)
                # if message has attachments add them
                if message.attachments:
                    for i in message.attachments:
                        embedMessage.set_image(url=i.proxy_url)

            # Send to the desired channel
            await channelTo.send(embed=embedMessage)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["slow"])
    async def slowmode(self, ctx, seconds: int):
        if seconds > 21600 or seconds < 0:
            return await ctx.send("Seconds can't be above '21600' or less then '0'")

        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"Set the slowmode delay in this channel to {seconds} seconds!")


async def setup(bot):
    await bot.add_cog(Mod(bot))
