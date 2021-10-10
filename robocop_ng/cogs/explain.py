from discord import Embed, Colour
from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext, SlashContext


class Explainer(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.explanations = {
            "shaders": {
                "description": """Shaders are small programs running on a graphic card that are responsible for rendering graphics like terrain, characters, explosions, grass etc. Since a PC cannot directly execute Switch shaders these have to be translated into a format a PC can understand. This translation process is time consuming and you'll notice it in two ways:
\n1). Any new shaders that are encountered will cause the emulation to pause until the translation is done, which causes stuttering and FPS drops. When you load a game for the first time a lot of translation will happen, but by playing more this stuttering decreases rapidly.
\n2). Ryujinx will save any shaders a game uses (aka it caches them). When you launch a game Ryujinx will take some time loading those saved shaders to prevent the stuttering from happening again.""",
                "title": "Shaders & Shader Caches explained",
            },
            "pptc": {
                "description": """PPTC is CPU instructions""",
                "title": "PPTC explained",
            },
        }

    @cog_ext.cog_slash(name="shaders")
    async def shaders(self, ctx: SlashContext):
        print(self.explanations["shaders"]["title"])
        embed = Embed(
            title=self.explanations["shaders"]["title"],
            description=self.explanations["shaders"]["description"],
            colour=Colour(0x4A90E2),
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="pptc")
    async def pptc(self, ctx: SlashContext):
        embed = Embed(
            title=self.explanations["pptc"]["title"],
            description=self.explanations["pptc"]["description"],
            colour=Colour(0x4A90E2),
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="test")
    async def test(self, ctx: SlashContext):
        embed = Embed(
            title="Test",
            description="For testing only",
            colour=Colour(0x4A90E2),
        )
        await ctx.send(embed=embed)


def setup(bot: Bot):
    bot.add_cog(Explainer(bot))
