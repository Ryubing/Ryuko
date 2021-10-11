from discord import Embed, Colour
from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext, SlashContext
import config


class Explainer(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.ryujinx_blue = Colour(0x4A90E2)
        self.explanations = {
            "shaders": {
                "body_text": """Shaders are small programs running on a graphic card that are responsible for rendering graphics like terrain, characters, explosions, grass etc. Since a PC cannot directly execute Switch shaders these have to be translated into a format a PC can understand. This translation process is time consuming and you'll notice it in two ways:
                                \n1). Any new shaders that are encountered will cause the emulation to pause until the translation is done, which causes stuttering and FPS drops. When you load a game for the first time a lot of translation will happen, but by playing more this stuttering decreases rapidly.
                                \n2). Ryujinx will save any shaders a game uses (aka it caches them). When you launch a game Ryujinx will take some time loading those saved shaders to prevent the stuttering from happening again.
                                \nFor a more technical explanation see here: https://blog.ryujinx.org/shader-cache-is-finally-here/""",
                "title": "Shaders & Shader Caches explained",
            },
            "pptc": {
                "body_text": """PPTC (Profiled Persistent Translation Cache) is a cache of translated CPU instructions. This speeds up games by having the already translated functions be in a readily accessible location, since translation has already been done.
                                After enabling PPTC from the emulator GUI, you need 3 boots for the full effect:
                                \n1) During the first boot of a title, a profiling file (.info) is created or updated.
                                \n2) At the second boot of the title the already saved profiling information is used to decide which new functions must be translated and how. Any function not translated will be translated at the next run; at the end of this phase a cache file (.cache) is created and the execution continues.
                                \n3) At the third boot of the title the already translated and saved functions are used to speed up the loading of the title.
                                \nFor a more technical explanation see: https://blog.ryujinx.org/introducing-profiled-persistent-translation-cache/""",
                "title": "PPTC & PPTC Caches explained",
            },
            "logs": {
                "body_text": """Log files are saved in are saved in the `Logs` folder.
                                Access this by doing `File > Open Log Folder` in Ryujinx, or by going to the folder directly where your `Ryujinx.exe` (Windows) or `Ryujinx` binary (Linux) is located.
                                The last 3 logs from the last 3 boots of Ryujinx will be available. For support purposes, you'll usually want to drag and drop the largest one into Discord.""",
                "title": "How to get log files",
            },
            "support": {
                "body_text": f"""Please use <#{config.bot_log_allowed_channels["support"]}>, <#{config.bot_log_allowed_channels['patreon-support']}> or <#{config.bot_log_allowed_channels['linux-master-race']}> channels to get help.
                                The easiest way to get help is to post a log file, since that will have information on your specs and hardware:
                                \nLog files are saved in are saved in the `Logs` folder.
                                Access this by doing `File > Open Log Folder` in Ryujinx, or by going to the folder directly where your `Ryujinx.exe` (Windows) or `Ryujinx` binary (Linux) is located.
                                The last 3 logs from the last 3 boots of Ryujinx will be available. For support purposes, you'll usually want to drag and drop the largest one into Discord.
                                \nIf you are unable to provide a log file, please provide your basic specs including: Ryujinx version, CPU model, GPU model and RAM amount, as well as **the name of the game and the version of the game you're having issues with.**
                                \n**Please be patient. Someone will help if you if they can and are available, but please also be mindful of people's time.**""",
                "title": "Getting support for Ryujinx",
            },
            "keys": {
                "body_text": """Prod.keys are the decryption keys that allow the emulator to run commercial software. Each key is **unique to a console**, you must dump it from the device that you've bought since you only have a licence to that specific device.
                                \nTo dump keys and firmware from your Switch, follow this guide: https://nh-server.github.io/switch-guide/user_guide/sysnand/making_essential_backups/""",
                "title": "Prod.keys & dumping explained",
            },
            "firmware": {
                "body_text": """Firmware files contain the Switch OS (codenamed Horizon) as well as some small apps like the Home menu and the Mii applet. Occasionally some games may require a firmware upgrade in order to be playable.
                                \nTo dump keys and firmware from your Switch, follow this guide: https://nh-server.github.io/switch-guide/user_guide/sysnand/making_essential_backups/""",
                "title": "Firmware dumping explained",
            },
        }

    @cog_ext.cog_slash(
        name="shaders", description="Explains how shaders and shader caches work."
    )
    async def explain_shaders(self, ctx: SlashContext):
        embed = Embed(
            title=self.explanations["shaders"]["title"],
            description=self.explanations["shaders"]["body_text"],
            colour=self.ryujinx_blue,
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="pptc", description="Explains how PPTC caches work.")
    async def explain_pptc(self, ctx: SlashContext):
        embed = Embed(
            title=self.explanations["pptc"]["title"],
            description=self.explanations["pptc"]["body_text"],
            colour=self.ryujinx_blue,
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="logs", description="How to get Ryujinx log files.")
    async def explain_logs(self, ctx: SlashContext):
        embed = Embed(
            title=self.explanations["logs"]["title"],
            description=self.explanations["logs"]["body_text"],
            colour=self.ryujinx_blue,
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="support", description="How to get help with Ryujinx.")
    async def get_support(self, ctx: SlashContext):
        embed = Embed(
            title=self.explanations["support"]["title"],
            description=self.explanations["support"]["body_text"],
            colour=self.ryujinx_blue,
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="keys", description="How to dump prod.keys file.")
    async def get_support(self, ctx: SlashContext):
        embed = Embed(
            title=self.explanations["keys"]["title"],
            description=self.explanations["keys"]["body_text"],
            colour=self.ryujinx_blue,
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="firmware", description="How to dump system firmware.")
    async def get_support(self, ctx: SlashContext):
        embed = Embed(
            title=self.explanations["firmware"]["title"],
            description=self.explanations["firmware"]["body_text"],
            colour=self.ryujinx_blue,
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="test", description="A simple test command.")
    async def test(self, ctx: SlashContext):
        embed = Embed(
            title="Test",
            description="For testing only",
            colour=self.ryujinx_blue,
        )
        await ctx.send(embed=embed)


def setup(bot: Bot):
    bot.add_cog(Explainer(bot))
