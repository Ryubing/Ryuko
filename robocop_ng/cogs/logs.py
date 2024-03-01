import json
import os
import re

import discord
from discord.ext.commands import Cog

from robocop_ng.helpers.checks import check_if_staff
from robocop_ng.helpers.invites import get_invites, set_invites
from robocop_ng.helpers.restrictions import get_user_restrictions
from robocop_ng.helpers.userlogs import get_userlog


class Logs(Cog):
    """
    Logs join and leave messages, bans and unbans, and member changes.
    """

    def __init__(self, bot):
        self.bot = bot
        self.invite_re = re.compile(
            r"((discord\.gg|discordapp\.com/" r"+invite)/+[a-zA-Z0-9-]+)", re.IGNORECASE
        )
        self.name_re = re.compile(r"[a-zA-Z0-9].*")
        self.clean_re = re.compile(r"[^a-zA-Z0-9_ ]+", re.UNICODE)
        # All lower case, no spaces, nothing non-alphanumeric
        susp_hellgex = "|".join(
            [r"\W*".join(list(word)) for word in self.bot.config.suspect_words]
        )
        self.susp_hellgex = re.compile(susp_hellgex, re.IGNORECASE)

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()

        if member.guild.id not in self.bot.config.guild_whitelist:
            return

        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        # We use this a lot, might as well get it once
        escaped_name = self.bot.escape_message(member)

        # Attempt to correlate the user joining with an invite
        invites = get_invites(self.bot)

        real_invites = await member.guild.invites()

        # Add unknown active invites. Can happen if invite was manually created
        for invite in real_invites:
            if invite.id not in invites:
                invites[invite.id] = {
                    "uses": 0,
                    "url": invite.url,
                    "max_uses": invite.max_uses,
                    "code": invite.code,
                }

        probable_invites_used = []
        items_to_delete = []
        # Look for invites whose usage increased since last lookup
        for id, invite in invites.items():
            real_invite = next((x for x in real_invites if x.id == id), None)

            if real_invite is None:
                # Invite does not exist anymore. Was either revoked manually
                # or the final use was used up
                probable_invites_used.append(invite)
                items_to_delete.append(id)
            elif invite["uses"] < real_invite.uses:
                probable_invites_used.append(invite)
                invite["uses"] = real_invite.uses

        # Delete used up invites
        for id in items_to_delete:
            del invites[id]

        # Save invites data.
        set_invites(self.bot, invites)

        # Prepare the invite correlation message
        if len(probable_invites_used) == 1:
            invite_used = probable_invites_used[0]["code"]
        elif len(probable_invites_used) == 0:
            invite_used = "Unknown"
        else:
            invite_used = "One of: "
            invite_used += ", ".join([x["code"] for x in probable_invites_used])

        # Check if user account is older than 15 minutes
        age = member.joined_at - member.created_at
        if age < self.bot.config.min_age:
            try:
                await member.send(
                    f"Your account is too new to "
                    f"join {member.guild.name}."
                    " Please try again later."
                )
                sent = True
            except discord.errors.Forbidden:
                sent = False
            await member.kick(reason="Too new")

            msg = (
                f"🚨 **Account too new**: {member.mention} | "
                f"{escaped_name}\n"
                f"🗓 __Creation__: {member.created_at}\n"
                f"🕓 Account age: {age}\n"
                f"✉ Joined with: {invite_used}\n"
                f"🏷 __User ID__: {member.id}"
            )
            if not sent:
                msg += (
                    "\nThe user has disabled direct messages, "
                    "so the reason was not sent."
                )
            await log_channel.send(msg)
            return
        msg = (
            f"✅ **Join**: {member.mention} | "
            f"{escaped_name}\n"
            f"🗓 __Creation__: {member.created_at}\n"
            f"🕓 Account age: {age}\n"
            f"✉ Joined with: {invite_used}\n"
            f"🏷 __User ID__: {member.id}"
        )

        # Handles user restrictions
        # Basically, gives back muted role to users that leave with it.
        rsts = get_user_restrictions(self.bot, member.id)
        roles = [discord.utils.get(member.guild.roles, id=rst) for rst in rsts]
        await member.add_roles(*roles)

        # Real hell zone.
        warns = get_userlog(self.bot)
        try:
            if len(warns[str(member.id)]["warns"]) == 0:
                await log_channel.send(msg)
            else:
                embed = discord.Embed(
                    color=discord.Color.dark_red(), title=f"Warns for {escaped_name}"
                )
                embed.set_thumbnail(url=str(member.display_avatar))
                for idx, warn in enumerate(warns[str(member.id)]["warns"]):
                    embed.add_field(
                        name=f"{idx + 1}: {warn['timestamp']}",
                        value=f"Issuer: {warn['issuer_name']}"
                        f"\nReason: {warn['reason']}",
                    )
                await log_channel.send(msg, embed=embed)
        except KeyError:  # if the user is not in the file
            await log_channel.send(msg)

    async def do_spy(self, message):
        if message.author.bot:
            return

        if check_if_staff(message):
            return

        alert = False
        cleancont = self.clean_re.sub("", message.content).lower()
        msg = (
            f"🚨 Suspicious message by {message.author.mention} "
            f"({message.author.id}):"
        )

        invites = self.invite_re.findall(message.content)
        for invite in invites:
            msg += f"\n- Has invite: https://{invite[0]}"
            alert = True

        for susp_word in self.bot.config.suspect_words:
            if susp_word in cleancont and not any(
                ok_word in cleancont
                for ok_word in self.bot.config.suspect_ignored_words
            ):
                msg += f"\n- Contains suspicious word: `{susp_word}`"
                alert = True

        if alert:
            msg += f"\n\nJump: <{message.jump_url}>"
            spy_channel = self.bot.get_channel(self.bot.config.spylog_channel)

            # Bad Code :tm:, blame retr0id
            message_clean = message.content.replace("*", "").replace("_", "")
            regd = self.susp_hellgex.sub(
                lambda w: "**{}**".format(w.group(0)), message_clean
            )

            # Show a message embed
            embed = discord.Embed(description=regd)
            embed.set_author(
                name=message.author.display_name,
                icon_url=str(message.author.display_avatar),
            )

            await spy_channel.send(msg, embed=embed)

    async def do_nickcheck(self, message):
        compliant = self.name_re.fullmatch(message.author.display_name)
        if compliant:
            return

        msg = (
            f"R11 violating name by {message.author.mention} " f"({message.author.id})."
        )

        spy_channel = self.bot.get_channel(self.bot.config.spylog_channel)
        await spy_channel.send(msg)

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if message.channel.id not in self.bot.config.spy_channels:
            return

        await self.do_spy(message)

    @Cog.listener()
    async def on_message_edit(self, before, after):
        await self.bot.wait_until_ready()
        if after.channel.id not in self.bot.config.spy_channels or after.author.bot:
            return

        # If content is the same, just skip over it
        # This usually means that something embedded.
        if before.clean_content == after.clean_content:
            return

        await self.do_spy(after)

        # U+200D is a Zero Width Joiner stopping backticks from breaking the formatting
        before_content = before.clean_content.replace("`", "`\u200d")
        after_content = after.clean_content.replace("`", "`\u200d")

        log_channel = self.bot.get_channel(self.bot.config.log_channel)

        msg = (
            "📝 **Message edit**: \n"
            f"from {self.bot.escape_message(after.author.name)} "
            f"({after.author.id}), in {after.channel.mention}:\n"
            f"```{before_content}``` → ```{after_content}```"
        )

        # If resulting message is too long, upload to hastebin
        if len(msg) > 2000:
            haste_url = await self.bot.haste(msg)
            msg = f"📝 **Message edit**: \nToo long: <{haste_url}>"

        await log_channel.send(msg)

    @Cog.listener()
    async def on_message_delete(self, message):
        await self.bot.wait_until_ready()
        if message.channel.id not in self.bot.config.spy_channels or message.author.bot:
            return

        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        msg = (
            "🗑️ **Message delete**: \n"
            f"from {self.bot.escape_message(message.author.name)} "
            f"({message.author.id}), in {message.channel.mention}:\n"
            f"`{message.clean_content}`"
        )

        # If resulting message is too long, upload to hastebin
        if len(msg) > 2000:
            haste_url = await self.bot.haste(msg)
            msg = f"🗑️ **Message delete**: \nToo long: <{haste_url}>"

        await log_channel.send(msg)

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()

        if member.guild.id not in self.bot.config.guild_whitelist:
            return

        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        msg = (
            f"⬅️ **Leave**: {member.mention} | "
            f"{self.bot.escape_message(member)}\n"
            f"🏷 __User ID__: {member.id}"
        )
        await log_channel.send(msg)

    @Cog.listener()
    async def on_member_ban(self, guild, member):
        await self.bot.wait_until_ready()

        if guild.id not in self.bot.config.guild_whitelist:
            return

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        msg = (
            f"⛔ **Ban**: {member.mention} | "
            f"{self.bot.escape_message(member)}\n"
            f"🏷 __User ID__: {member.id}"
        )
        await log_channel.send(msg)

    @Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.bot.wait_until_ready()

        if guild.id not in self.bot.config.guild_whitelist:
            return

        log_channel = self.bot.get_channel(self.bot.config.modlog_channel)
        msg = (
            f"⚠️ **Unban**: {user.mention} | "
            f"{self.bot.escape_message(user)}\n"
            f"🏷 __User ID__: {user.id}"
        )
        # if user.id in self.bot.timebans:
        #     msg += "\nTimeban removed."
        #     self.bot.timebans.pop(user.id)
        #     with open("data/timebans.json", "r") as f:
        #         timebans = json.load(f)
        #     if user.id in timebans:
        #         timebans.pop(user.id)
        #         with open("data/timebans.json", "w") as f:
        #             json.dump(timebans, f)
        await log_channel.send(msg)

    @Cog.listener()
    async def on_member_update(self, member_before, member_after):
        await self.bot.wait_until_ready()

        if member_after.guild.id not in self.bot.config.guild_whitelist:
            return

        msg = ""
        log_channel = self.bot.get_channel(self.bot.config.log_channel)
        if member_before.roles != member_after.roles:
            # role removal
            role_removal = []
            for index, role in enumerate(member_before.roles):
                if role not in member_after.roles:
                    role_removal.append(role)
            # role addition
            role_addition = []
            for index, role in enumerate(member_after.roles):
                if role not in member_before.roles:
                    role_addition.append(role)

            if len(role_addition) != 0 or len(role_removal) != 0:
                msg += "\n👑 __Role change__: "
                roles = []
                for role in role_removal:
                    roles.append("_~~" + role.name + "~~_")
                for role in role_addition:
                    roles.append("__**" + role.name + "**__")
                for index, role in enumerate(member_after.roles):
                    if role.name == "@everyone":
                        continue
                    if role not in role_removal and role not in role_addition:
                        roles.append(role.name)
                msg += ", ".join(roles)

        if member_before.name != member_after.name:
            msg += (
                "\n📝 __Username change__: "
                f"{self.bot.escape_message(member_before)} → "
                f"{self.bot.escape_message(member_after)}"
            )
        if member_before.nick != member_after.nick:
            if not member_before.nick:
                msg += "\n🏷 __Nickname addition__"
            elif not member_after.nick:
                msg += "\n🏷 __Nickname removal__"
            else:
                msg += "\n🏷 __Nickname change__"
            msg += (
                f": {self.bot.escape_message(member_before.nick)} → "
                f"{self.bot.escape_message(member_after.nick)}"
            )
        if msg:
            msg = (
                f"ℹ️ **Member update**: {member_after.mention} | "
                f"{self.bot.escape_message(member_after)}{msg}"
            )
            await log_channel.send(msg)


async def setup(bot):
    await bot.add_cog(Logs(bot))
