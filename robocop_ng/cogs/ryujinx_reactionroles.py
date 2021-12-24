import json
import config
import os

import discord
from discord.ext.commands import Cog


class RyujinxReactionRoles(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = (
            config.reaction_roles_channel_id
        )  # The channel to send the reaction role message. (self-roles channel)

        self.emoji_map = {
            "🦑": "Looking for LDN game (Splatoon 2)",
            "👹": "Looking for LDN game (Monster Hunter Generations Ultimate)",
            "👺": "Looking for LDN game (Monster Hunter Rise)",
            "🧩": "Looking for LDN game (Mario Party Superstars)",
            "🐉": "Looking for LDN game (Pokémon Sword/Shield)",
            "⚔️": "Looking for LDN game (Super Smash Bros. Ultimate)",
            "🏎️": "Looking for LDN game (Mario Kart 8)",
            "🪨": "Looking for LDN game (Pokémon Brilliant Diamond/Shining Pearl)",
            "🍃": "Looking for LDN game (Animal Crossing: New Horizons)",
            "➡": "Looking for LDN game (Others)",
            "🚩": "Testers",
            # LDN roles should be placed *before* testers role, because of embed generating.
            # LDN roles ought to be in the format "Looking for LDN game (<game>)".
        }  # The mapping of emoji ids to the role.

        self.file = "data/reactionroles.json"  # the file to store the required reaction role data. (message id of the RR message.)

        self.msg_id = None
        self.m = None  # the msg object

        self.get_role = lambda emoji_name: discord.utils.get(
            self.bot.guilds[0].roles,
            name=self.emoji_map.get(str(emoji_name)),
        )

    async def generate_embed(self):
        emojis = list(self.emoji_map.keys())
        description = "React to this message with the emojis given below to get your 'Looking for LDN game' roles. \n\n"

        for x in emojis:
            if self.emoji_map.get(x) == "Testers":
                description += f'\nReact {x} to get the "{self.emoji_map.get(x)}" role.'
            else:
                description += (
                    f"{x} for __{self.emoji_map.get(x).split('(')[1].split(')')[0]}__ \n"
                )

        embed = discord.Embed(
            title="**Select your roles**", description=description, color=420420
        )
        embed.set_footer(
            text="To remove a role, simply remove the corresponding reaction."
        )

        return embed

    async def handle_offline_reaction_add(self):
        for reaction in self.m.reactions:
            for user in await reaction.users().flatten():
                if self.emoji_map.get(reaction.emoji) is not None:
                    role = self.get_role(reaction.emoji)
                    if not user in role.members and not user.bot:
                        await user.add_roles(role)
                else:
                    await self.m.clear_reaction(reaction.emoji)

    async def handle_offline_reaction_remove(self):
        for emoji in self.emoji_map:
            for reaction in self.m.reactions:
                role = self.get_role(reaction.emoji)
                for user in role.members:
                    if user not in await reaction.users().flatten():
                        await self.m.guild.get_member(user.id).remove_roles(role)

    @Cog.listener()
    async def on_ready(self):

        guild = self.bot.guilds[0]  # The ryu guild in which the bot is.
        channel = guild.get_channel(self.channel_id)

        if not os.path.exists(self.file):
            with open(self.file, "w") as f:
                f.write("{}")

        with open(self.file, "r") as f:
            id = json.load(f).get("id")

        m = discord.utils.get(await channel.history().flatten(), id=id)
        if m is None:
            os.remove(self.file)

            embed = await self.generate_embed()
            self.m = await channel.send(embed=embed)
            self.msg_id = self.m.id

            for x in self.emoji_map:
                await self.m.add_reaction(x)

            with open(self.file, "w") as f:
                json.dump({"id": self.m.id}, f)

            await self.handle_offline_reaction_remove()

        else:
            self.m = discord.utils.get(await channel.history().flatten(), id=id)
            self.msg_id = self.m.id

            await self.m.edit(embed=await self.generate_embed())
            for x in self.emoji_map:
                if not x in self.m.reactions:
                    await self.m.add_reaction(x)

            await self.handle_offline_reaction_add()
            await self.handle_offline_reaction_remove()

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            pass
        else:
            if payload.message_id == self.msg_id:
                if self.emoji_map.get(payload.emoji.name) is not None:
                    if self.get_role(payload.emoji.name) is not None:
                        await payload.member.add_roles(
                            self.get_role(payload.emoji.name)
                        )
                    else:
                        print(f"Role {self.emoji_map[payload.emoji.name]} not found.")
                else:
                    await self.m.clear_reaction(payload.emoji.name)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id == self.msg_id:
            if self.emoji_map.get(str(payload.emoji.name)) is not None:

                guild = discord.utils.find(
                    lambda guild: guild.id == payload.guild_id, self.bot.guilds
                )

                await guild.get_member(payload.user_id).remove_roles(
                    self.get_role(payload.emoji.name)
                )  # payload.member.remove_roles will throw error


def setup(bot):
    bot.add_cog(RyujinxReactionRoles(bot))
