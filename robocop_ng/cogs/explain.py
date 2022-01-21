import config
from discord import Colour, Embed
from discord.ext.commands import Bot, Cog
from discord_slash import SlashContext, cog_ext


class Explainer(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.ryujinx_blue = Colour(0x4A90E2)
        self.explanations = {
            "shaders": {
                "body_text": """Shaders are small programs running on a graphic card that are responsible for rendering graphics like terrain, characters, explosions, grass etc. Since a PC cannot directly execute Switch shaders these have to be translated into a format a PC can understand. This translation process is time consuming and you'll notice it in two ways:
                                \n1) Any new shaders that are encountered will cause the emulation to pause until the translation is done, which causes stuttering and FPS drops. When you load a game for the first time a lot of translation will happen, but by playing more this stuttering decreases rapidly.
                                \n2) Ryujinx will save any shaders a game uses (aka it caches them). When you launch a game Ryujinx will take some time loading those saved shaders to prevent the stuttering from happening again.
                                \nFor a more technical explanation see here: https://blog.ryujinx.org/shader-cache-is-finally-here/
                                \n**NOTE: Shaders contain copyrighted game code so you must _generate your own_. Using third-party shaders is considered piracy.**""",
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
                                The easiest way to get help is to post a log file, since that will have information on your hardware specs and any common errors in your configuration.
                                \nLog files are saved in are saved in the `Logs` folder.
                                Access this by doing `File > Open Log Folder` in Ryujinx, or by going to the folder directly where your `Ryujinx.exe` (Windows) or `Ryujinx` binary (Linux) is located.
                                The last 3 logs from the last 3 boots of Ryujinx will be available. For support purposes, you'll usually want to upload the largest one into Discord.
                                \nIf you are unable to provide a log file, please provide your basic specs including: Ryujinx version, CPU model, GPU model and RAM amount, as well as **the name of the game and the version of the game you're having issues with (as well as any mods being used).**
                                \n**Please be patient. Someone will help if you if they can and are available, but please also be mindful of people's time.**""",
                "title": "Getting support for Ryujinx",
            },
            "keys": {
                "body_text": """The `prod.keys` file contains the decryption keys that allow the emulator to run commercial software. Each key is **unique to a console**, you must dump it from the device that you've bought since you only have a license to that specific device.
                                \nTo dump keys and firmware from your Switch, follow this guide: https://nh-server.github.io/switch-guide/user_guide/sysnand/making_essential_backups/""",
                "title": "Prod.keys & dumping explained",
            },
            "firmware": {
                "body_text": """Firmware files contain the Switch OS (codenamed Horizon) as well as some small apps like the Home menu and the Mii applet. Occasionally some games may require a Switch firmware upgrade in order to be playable.
                                \nTo dump keys and firmware from your Switch, follow this guide: https://nh-server.github.io/switch-guide/user_guide/sysnand/making_essential_backups/""",
                "title": "Firmware dumping explained",
            },
            "fifo": {
                "body_text": """FIFO (First In First Out) refers to the command queue for the emulated GPU.
                            Your CPU does the work to emulate the Switch GPU commands, so the FIFO percentage shown is the time spent actively processing these instructions.
                            A higher FIFO percentage is not strictly related to performance, you may have high framerates while also having high FIFO and vice versa. Generally a high FIFO _could_ sometimes indicate an emulated GPU bottleneck.""",
                "title": "FIFO explained",
            },
            "default_logs": {
                "body_text": """Your default logging settings should have the following enabled:
                             \n`Logging to File`, `Stub Logs`, `Info Logs`, `Warning Logs`, `Error Logs` and `Guest Logs`.
                             \nRefer to the following screenshot:""",
                "image": "https://media.discordapp.net/attachments/410208610455519243/897471975570702336/unknown.png?width=582&height=609",
                "title": "Default Ryujinx logging settings",
            },
            "emulation_explain": {
                "body_text": """Games are programmed to work with specific hardware, which requires translating into something compatible with your PC. This process has to be done in real time as the emulated software is running, adding significant CPU overhead.
                            \nIt also often requires emulation of the hardware, so software is used to make a virtual version of the console. This is also very resource intensive (again, mostly on the CPU side).
                            \nNative PC games are optimized to run on modern processors with modern languages and architectures, so there are no performance overheads due to translation.
                            """,
                "title": "Emulation vs native PC games",
            },
            "amiibo": {
                "body_text": """Amiibo data is pulled from AmiiboAPI, so no dumping is needed. To use them in-game:
                \n1) Go to a section in the game where an Amiibo is requested, usually shown by an icon and a message screen asking to scan an Amiibo.
                2) In Ryujinx, select Tools > Scan an Amiibo.
                3) Choose the Amiibo you want to scan in.
                4) The game should recognize the Amiibo and you should see the effects as though you just scanned a real Amiibo figure.""",
                "image": "https://cdn.gamer-network.net/2020/usgamer/Animal-Crossing-New-Horizons-Photopia-Amiibo.jpg",
                "title": "Amiibos explained",
            },
            "docked_handheld_mode": {
                "body_text": """The Switch has two modes of operation: docked and handheld. Ryujinx can switch between these two.
                                \nDocked mode: The Switch GPU operates at a higher capacity since it does not have to worry about running off the battery.
                                This means games run at a higher resolution (1080p native) with some games having extra effects like higher draw distances or more anti-aliasing. This mode is slightly harder to emulate and requires more CPU power.
                                \nHandheld mode: The Switch console downclocks its GPU to save on battery. In this mode games run at 720p native resolution. In terms of emulation, those with underpowered hardware may benefit from this mode as it tends to be comparatively less intensive.""",
                "title": "Docked vs. Handheld mode",
            },
            "rule2": {
                "body_text": "Civil behavior is expected at all times. Disagreements with others are to be occasionally expected; however personal attacks of any kind (including derogatory slurs) are not tolerated and may result in an immediate ban.",
                "title": "Rule #2",
            },
            "rule3": {
                "body_text": """Do not spam, troll, or post content that is unrelated to the channel you are posting it in. Use common sense.\n
                                - No NSFW or pirated content.
                                - No self-advertising.""",
                "title": "Rule #3",
            },
            "rule4": {
                "body_text": """**This server does not support piracy.**
                                To use Ryujinx legally you must use your own Switch console and your own games.\n
                                - No help or support will be given to anyone who uses pirated games, keys, shaders or other files.
                                - No discussion on leaked games.
                                - No discussion on how to pirate games, keys, shaders or other files.
                                - No discussion on why you think piracy should be allowed.
                                \nWe are not here to argue. Please forward all complaints about copyright law to your local government's copyright enforcement agency.
                                """,
                "title": "Rule #4",
            },
            "rule5": {
                "body_text": "No custom builds are to be posted or discussed in the server. Requests for support of a custom build will be denied.",
                "title": "Rule #5",
            },
            "rule6": {
                "body_text": """Warnings will be issued for violations of the rules, for consistently skirting the rules/attempting to find loopholes for rule breaking, or for disregarding or protesting direction from Staff/Admins.\n
                                - Three warnings will result in a kick.
                                - The 4th warning will result in a ban.
                                - Attempting to evade or mitigate disciplinary action by leaving the server, using alts, etc. will result in an immediate ban."""
            },
        }

    def generate_embed(self, name):
        return Embed(
            title=self.explanations[name]["title"],
            description=self.explanations[name]["body_text"],
            colour=self.ryujinx_blue,
        )

    @cog_ext.cog_slash(
        name="logs", description="Explains how to get Ryujinx log files."
    )
    async def send_embed_logs(self, ctx: SlashContext):
        embed = self.generate_embed("logs")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="shaders", description="Explains shaders and shader caches."
    )
    async def send_embed_shaders(self, ctx: SlashContext):
        embed = self.generate_embed("shaders")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="pptc", description="Explains how PPTC caches work.")
    async def send_embed_pptc(self, ctx: SlashContext):
        embed = self.generate_embed("pptc")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="support", description="How to get support for Ryujinx.")
    async def send_embed_support(self, ctx: SlashContext):
        embed = self.generate_embed("support")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="keys", description="How to get keys for Ryujinx.")
    async def send_embed_keys(self, ctx: SlashContext):
        embed = self.generate_embed("keys")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="firmware", description="How to get firmware for Ryujinx.")
    async def send_embed_firmware(self, ctx: SlashContext):
        embed = self.generate_embed("firmware")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="fifo", description="Explains what FIFO is.")
    async def send_embed_fifo(self, ctx: SlashContext):
        embed = self.generate_embed("fifo")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="default_logs", description="The default Ryujinx logging settings."
    )
    async def send_embed_default_logs(self, ctx: SlashContext):
        embed = self.generate_embed("default_logs")
        embed.set_image(url=self.explanations["default_logs"]["image"])
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="emulation_explain",
        description="Explains why emulation is different from native gaming.",
    )
    async def send_embed_emulation_explain(self, ctx: SlashContext):
        embed = self.generate_embed("emulation_explain")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="amiibo", description="How to use Amiibos in Ryujinx.")
    async def send_embed_amiibo(self, ctx: SlashContext):
        embed = self.generate_embed("amiibo")
        embed.set_image(url=self.explanations["amiibo"]["image"])
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="docked_vs_handheld",
        description="Explains difference between docked and handheld modes.",
    )
    async def send_embed_docked_handheld(self, ctx: SlashContext):
        embed = self.generate_embed("docked_handheld_mode")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="r2", description="Explains civil behavior rule.")
    async def send_embed_civil(self, ctx: SlashContext):
        embed = self.generate_embed("rule2")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="r3", description="Explains content rule.")
    async def send_embed_troll(self, ctx: SlashContext):
        embed = self.generate_embed("rule3")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="r4", description="Explains anti-piracy rule.")
    async def send_embed_piracy(self, ctx: SlashContext):
        embed = self.generate_embed("rule4")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="r5", description="Explains custom builds rule.")
    async def send_embed_custom_build(self, ctx: SlashContext):
        embed = self.generate_embed("rule5")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="r6", description="Explains how warnings work.")
    async def send_embed_warnings(self, ctx: SlashContext):
        embed = self.generate_embed("rule6")
        await ctx.send(embed=embed)


def setup(bot: Bot):
    bot.add_cog(Explainer(bot))
