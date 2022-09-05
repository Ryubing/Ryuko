import collections
import json
import config
import os

import discord
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff

class RyujinxReactionRoles(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = (
            config.reaction_roles_channel_id
        )  # The channel to send the reaction role message. (self-roles channel)

        self.file = "data/reactionroles.json"  # the file to store the required reaction role data. (message id of the RR message.)

        self.msg_id = None
        self.m = None  # the msg object

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def register_reaction_role(self, ctx, target_role_id: int, emoji_name: str):
        """Register a reaction role, staff only."""

        if emoji_name[0] == '<':
            emoji_name = emoji_name[1:-1]

        if target_role_id in config.staff_role_ids:
            return await ctx.send("Error: Dangerous role found!")

        target_role = ctx.guild.get_role(target_role_id)

        if target_role is None:
            return await ctx.send("Error: Role not found!")

        target_role_name = target_role.name

        for key in self.reaction_config["reaction_roles_emoji_map"]:
            value = self.reaction_config["reaction_roles_emoji_map"][key]
            if type(value) is str and target_role_name == value:
                return await ctx.send(f"Error: {target_role_name}: already registered.")

        self.reaction_config["reaction_roles_emoji_map"][emoji_name] = target_role_name
        self.save_reaction_config(self.reaction_config)
        await self.reload_reaction_message(False)

        await ctx.send(f"{target_role_name}: registered.")

    def get_emoji_full_name(self, emoji):
        emoji_name = emoji.name
        if emoji_name is not None and emoji.id is not None:
            emoji_name = f":{emoji_name}:{emoji.id}"

        return emoji_name

    def get_role(self, key):
        return discord.utils.get(
            self.bot.guilds[0].roles,
            name=self.get_role_from_emoji(key),
        )

    def get_role_from_emoji(self, key):
        value = self.emoji_map.get(key)

        if value is not None and type(value) is not str:
            return value.get("role")

        return value

    async def generate_embed(self):
        last_descrption = []
        description = ["React to this message with the emojis given below to get your 'Looking for LDN game' roles. \n"]

        for x in self.emoji_map:
            value = self.emoji_map[x]

            emoji = x
            if len(emoji.split(':')) == 3:
                emoji = f"<{emoji}>"

            if type(value) is str:

                description.append(f"{emoji} for __{self.emoji_map.get(x).split('(')[1].split(')')[0]}__")
            else:
                role_name = value["role"]
                line_fmt = value["fmt"]
                if value.get("should_be_last", False):
                    last_descrption.append(line_fmt.format(emoji, role_name))
                else:
                    description.append(line_fmt.format(emoji, role_name))

        embed = discord.Embed(
            title="**Select your roles**", description='\n'.join(description) + '\n' + '\n'.join(last_descrption), color=420420
        )
        embed.set_footer(
            text="To remove a role, simply remove the corresponding reaction."
        )

        return embed

    async def handle_offline_reaction_add(self):
        for reaction in self.m.reactions:
            for user in await reaction.users().flatten():
                emoji_name = str(reaction.emoji)
                if emoji_name[0] == '<':
                    emoji_name = emoji_name[1:-1]

                if self.get_role_from_emoji(emoji_name) is not None:
                    role = self.get_role(emoji_name)
                    if not user in role.members and not user.bot:
                        await user.add_roles(role)
                else:
                    await self.m.clear_reaction(reaction.emoji)

    async def handle_offline_reaction_remove(self):
        for emoji in self.emoji_map:
            for reaction in self.m.reactions:
                emoji_name = str(reaction.emoji)
                if emoji_name[0] == '<':
                    emoji_name = emoji_name[1:-1]

                role = self.get_role(emoji_name)
                for user in role.members:
                    if user not in await reaction.users().flatten():
                        await self.m.guild.get_member(user.id).remove_roles(role)

    def load_reaction_config(self):
        if not os.path.exists(self.file):
            self.bot.log.error("HERE?!")
            with open(self.file, "w") as f:
                json.dump({}, f)

        with open(self.file, "r") as f:
            return json.load(f)

    def save_reaction_config(self, value):
        with open(self.file, "w") as f:
            json.dump(value, f)

    async def reload_reaction_message(self, should_handle_offline = True):
        self.emoji_map = collections.OrderedDict(sorted(self.reaction_config["reaction_roles_emoji_map"].items(), key=lambda x: str(x[1])))


        guild = self.bot.guilds[0]  # The ryu guild in which the bot is.
        channel = guild.get_channel(self.channel_id)

        m = discord.utils.get(await channel.history().flatten(), id=self.reaction_config["id"])
        if m is None:
            self.reaction_config["id"] = None

            embed = await self.generate_embed()
            self.m = await channel.send(embed=embed)
            self.msg_id = self.m.id

            for x in self.emoji_map:
                await self.m.add_reaction(x)

            self.reaction_config["id"] = self.m.id
            self.save_reaction_config(self.reaction_config)

            await self.handle_offline_reaction_remove()

        else:
            self.m = discord.utils.get(await channel.history().flatten(), id=self.reaction_config["id"])
            self.msg_id = self.m.id

            await self.m.edit(embed=await self.generate_embed())
            for x in self.emoji_map:
                if not x in self.m.reactions:
                    await self.m.add_reaction(x)

            if should_handle_offline:
                await self.handle_offline_reaction_add()
                await self.handle_offline_reaction_remove()

    @Cog.listener()
    async def on_ready(self):
        self.reaction_config = self.load_reaction_config()

        await self.reload_reaction_message()

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            pass
        else:
            if payload.message_id == self.msg_id:
                emoji_name = self.get_emoji_full_name(payload.emoji)

                if self.get_role_from_emoji(emoji_name) is not None:
                    target_role = self.get_role(emoji_name)

                    if target_role is not None:
                        await payload.member.add_roles(
                            target_role
                        )
                    else:
                        self.bot.log.error(f"Role {self.emoji_map[emoji_name]} not found.")
                        await self.m.clear_reaction(payload.emoji)
                else:
                    await self.m.clear_reaction(payload.emoji)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id == self.msg_id:
            emoji_name = self.get_emoji_full_name(payload.emoji)

            if self.get_role_from_emoji(emoji_name) is not None:

                guild = discord.utils.find(
                    lambda guild: guild.id == payload.guild_id, self.bot.guilds
                )

                target_role = self.get_role(emoji_name)

                if target_role is not None:
                    await guild.get_member(payload.user_id).remove_roles(
                        self.get_role(emoji_name)
                    )  # payload.member.remove_roles will throw error


def setup(bot):
    bot.add_cog(RyujinxReactionRoles(bot))
