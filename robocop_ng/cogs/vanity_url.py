from discord import Guild
from discord.errors import Forbidden
from discord.ext import tasks
from discord.ext.commands import Cog


class VanityUrl(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vanity_codes: dict[int, str] = self.bot.config.vanity_codes
        self.check_changed_vanity_codes.start()

    def cog_unload(self):
        self.check_changed_vanity_codes.cancel()

    async def update_vanity_code(self, guild: Guild, code: str):
        if "VANITY_URL" in guild.features and guild.vanity_url_code != code:
            try:
                await guild.edit(
                    reason="Configured vanity code was different", vanity_code=code
                )
            except Forbidden:
                self.bot.log.exception(f"Not allowed to edit vanity url for: {guild}")
                self.cog_unload()
                await self.bot.unload_extension("robocop_ng.cogs.vanity_url")

    @Cog.listener()
    async def on_guild_update(self, before: Guild, after: Guild):
        if after.id in self.vanity_codes:
            await self.update_vanity_code(after, self.vanity_codes[after.id])

    @tasks.loop(hours=12)
    async def check_changed_vanity_codes(self):
        await self.bot.wait_until_ready()
        for guild, vanity_code in self.vanity_codes.items():
            await self.update_vanity_code(self.bot.get_guild(guild), vanity_code)


async def setup(bot):
    await bot.add_cog(VanityUrl(bot))
