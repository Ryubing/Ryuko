import json
import config
import os

import discord
from discord.ext.commands import Cog


class RyujinxReactionRoles(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = (
            config.reaction_roles_channel_id # The channel to send the reaction role message. (self-roles channel)
        )  
        self.emoji_map = {
            "🦑": "Looking for LDN game (Splatoon 2)",
            "👹": "Looking for LDN game (Monster Hunter Generations Ultimate)",
            "👺": "Looking for LDN game (Monster Hunter Rise)",
            "⚔️": "Looking for LDN game (Super Smash Bros. Ultimate)",
            "🏎️": "Looking for LDN game (Mario Kart 8)",
            "🍃": "Looking for LDN game (Animal Crossing: New Horizons)",
            "➡": "Looking for LDN game (Others)",
            "🚩": "Testers",
        }  # The mapping of emoji ids to the role.
        self.file = "data/reactionroles.json"  # the file to store the required reaction role data. (message id of the RR message.)

    async def handle_offline_reaction_add(self, m):
        for x in m.reactions:
                for y in await x.users().flatten():
                    if self.emoji_map.get(x.emoji) is not None:
                        role = discord.utils.get(
                            m.guild.roles, name=self.emoji_map[str(x.emoji)]
                        )
                        if not y in role.members and not y.bot:
                            await m.guild.get_member(y.id).add_roles(role)
                    else:
                        await m.clear_reaction(x.emoji)

    async def handle_offline_reaction_remove(self, m):
        for x in self.emoji_map:
            role = discord.utils.get(m.guild.roles, name=self.emoji_map[x])
            for x in m.reactions:
                for y in role.members:
                    if y not in await x.users().flatten():
                        await m.guild.get_member(y.id).remove_roles(role)

    @Cog.listener()
    async def on_ready(self):
    
        guild = self.bot.guilds[0]  # The ryu guild in which the bot is.
        channel = guild.get_channel(self.channel_id)

        if not os.path.exists(self.file):
            with open(self.file, "w") as f:
                f.write("{}")

        with open(self.file, "r") as f:
            msg = json.load(f)

        m = discord.utils.get(await channel.history().flatten(), id=msg.get("id"))

        if m is None:
            os.remove(self.file)
            description = """
          _React to this message to get your "Looking for LDN game" roles._
          🦑 Splatoon 2
          👹 Monster Hunter Generations Ultimate
          👺 Monster Hunter Rise
          🏎️ Mario Kart 8 (Deluxe)
          🍃 Animal Crossing: New Horizons 
          ⚔️ Super Smash Bros Ultimate 
          ➡ Others

          React 🚩 to get "Testers" Role.
                         """
            embed = discord.Embed(
                title="**Select your roles**", description=description, color=27491
            )
            embed.set_footer(text="To remove the role, simply remove the reaction.")
            message = await channel.send(embed=embed)

            for x in self.emoji_map:
                await message.add_reaction(x)

            with open(self.file, "w") as f:
                json.dump({"id": message.id}, f)
        
        m = discord.utils.get(await channel.history().flatten(), id=msg.get("id"))
        
        await self.handle_offline_reaction_add(m)
        await self.handle_offline_reaction_remove(m)
            
    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            pass
        else:
            with open(self.file, "r") as f:
                msg_id = json.load(f).get("id")  # Get the ID
            if payload.message_id == msg_id:
                if self.emoji_map.get(payload.emoji.name) is not None:
                    role = discord.utils.get(
                        self.bot.get_guild(payload.guild_id).roles,
                        name=self.emoji_map[str(payload.emoji.name)],
                    )
                    if role is not None:
                        await payload.member.add_roles(role)
                    else:
                        print(f"Role {self.emoji_map[payload.emoji.name]} not found.")
                else:
                    m = discord.utils.get(
                        await self.bot.guilds[0]
                        .get_channel(self.channel_id)
                        .history()
                        .flatten(),
                        id=msg_id,
                    )
                    await m.clear_reaction(payload.emoji.name)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        with open(self.file, "r") as f:
            msg_id = json.load(f).get("id")
        if payload.message_id == msg_id:
            if self.emoji_map[str(payload.emoji.name)]:

                guild = discord.utils.find(
                    lambda guild: guild.id == payload.guild_id, self.bot.guilds
                )

                role = discord.utils.get(
                    self.bot.get_guild(payload.guild_id).roles,
                    name = self.emoji_map[str(payload.emoji.name)],
                )

                await guild.get_member(payload.user_id).remove_roles(   # payload.member.remove_roles will throw error
                    role
                ) 


def setup(bot):
    bot.add_cog(RyujinxReactionRoles(bot))
