import logging
import re

import aiohttp
from discord import Colour, Embed, Message, Attachment
from discord.ext import commands
from discord.ext.commands import Cog, Context, BucketType

from robocop_ng.helpers.checks import check_if_staff
from robocop_ng.helpers.disabled_ids import (
    add_disabled_app_id,
    is_app_id_valid,
    remove_disabled_app_id,
    get_disabled_ids,
    is_app_id_disabled,
    is_build_id_valid,
    add_disabled_build_id,
    remove_disabled_build_id,
    is_build_id_disabled,
    is_ro_section_disabled,
    is_ro_section_valid,
    add_disabled_ro_section,
    remove_disabled_ro_section,
    remove_disable_id,
)
from robocop_ng.helpers.ryujinx_log_analyser import LogAnalyser

logging.basicConfig(
    format="%(asctime)s (%(levelname)s) %(message)s (Line %(lineno)d)",
    level=logging.INFO,
)


class LogFileReader(Cog):
    @staticmethod
    def is_valid_log_name(attachment: Attachment) -> tuple[bool, bool]:
        filename = attachment.filename
        ryujinx_log_file_regex = re.compile(r"^Ryujinx_.*\.log$")
        log_file = re.compile(r"^.*\.log|.*\.txt$")
        is_ryujinx_log_file = re.match(ryujinx_log_file_regex, filename) is not None
        is_log_file = re.match(log_file, filename) is not None

        return is_log_file, is_ryujinx_log_file

    def __init__(self, bot):
        self.bot = bot
        self.bot_log_allowed_channels = self.bot.config.bot_log_allowed_channels
        self.disallowed_named_roles = ["pirate"]
        self.ryujinx_blue = Colour(0x4A90E2)
        self.uploaded_log_info = []

        self.disallowed_roles = [
            self.bot.config.named_roles[x] for x in self.disallowed_named_roles
        ]

    @staticmethod
    async def download_file(log_url):
        async with aiohttp.ClientSession() as session:
            # Grabs first and last few bytes of log file to prevent abuse from large files
            headers = {"Range": "bytes=0-60000, -6000"}
            async with session.get(log_url, headers=headers) as response:
                return await response.text("UTF-8")

    @staticmethod
    def is_log_valid(log_file: str) -> bool:
        app_info = LogAnalyser.get_app_info(log_file)
        is_homebrew = LogAnalyser.is_homebrew(log_file)
        if app_info is None or is_homebrew:
            return True
        game_name, app_id, another_app_id, build_ids, main_ro_section = app_info
        if (
            game_name is None
            or app_id is None
            or another_app_id is None
            or build_ids is None
            or main_ro_section is None
        ):
            return False
        return app_id == another_app_id

    def is_game_blocked(self, log_file: str) -> bool:
        app_info = LogAnalyser.get_app_info(log_file)
        if app_info is None:
            return False
        game_name, app_id, another_app_id, build_ids, main_ro_section = app_info
        if is_app_id_disabled(self.bot, app_id) or is_app_id_disabled(
            self.bot, another_app_id
        ):
            return True
        for bid in build_ids:
            if is_build_id_disabled(self.bot, bid):
                return True
        return is_ro_section_disabled(self.bot, main_ro_section)

    async def blocked_game_action(self, message: Message) -> Embed:
        warn_command = self.bot.get_command("warn")
        if warn_command is not None:
            warn_message = await message.reply(
                ".warn This log contains a blocked game."
            )
            warn_context = await self.bot.get_context(warn_message)
            await warn_context.invoke(
                warn_command,
                target=None,
                reason="This log contains a blocked game.",
            )
        else:
            logging.error(
                f"Couldn't find 'warn' command. Unable to warn {message.author}."
            )

        pirate_role = message.guild.get_role(self.bot.config.named_roles["pirate"])
        await message.author.add_roles(pirate_role)

        embed = Embed(
            title="⛔ Blocked game detected ⛔",
            colour=Colour(0xFF0000),
            description="This log contains a blocked game and has been removed.\n"
            "The user has been warned and the pirate role was applied.",
        )
        embed.set_footer(text=f"Log uploaded by @{message.author.name}")
        await message.delete()
        return embed

    def format_analysed_log(self, author_name: str, analysed_log):
        cleaned_game_name = re.sub(
            r"\s\[(64|32)-bit\]$", "", analysed_log["game_info"]["game_name"]
        )
        analysed_log["game_info"]["game_name"] = cleaned_game_name

        hardware_info = " | ".join(
            (
                f"**CPU:** {analysed_log['hardware_info']['cpu']}",
                f"**GPU:** {analysed_log['hardware_info']['gpu']}",
                f"**RAM:** {analysed_log['hardware_info']['ram']}",
                f"**OS:** {analysed_log['hardware_info']['os']}",
            )
        )

        system_settings_info = "\n".join(
            (
                f"**Audio Backend:** `{analysed_log['settings']['audio_backend']}`",
                f"**Console Mode:** `{analysed_log['settings']['docked']}`",
                f"**PPTC Cache:** `{analysed_log['settings']['pptc']}`",
                f"**Shader Cache:** `{analysed_log['settings']['shader_cache']}`",
                f"**V-Sync:** `{analysed_log['settings']['vsync']}`",
                f"**Hypervisor:** `{analysed_log['settings']['hypervisor']}`",
            )
        )

        graphics_settings_info = "\n".join(
            (
                f"**Graphics Backend:** `{analysed_log['settings']['graphics_backend']}`",
                f"**Resolution:** `{analysed_log['settings']['resolution_scale']}`",
                f"**Anisotropic Filtering:** `{analysed_log['settings']['anisotropic_filtering']}`",
                f"**Aspect Ratio:** `{analysed_log['settings']['aspect_ratio']}`",
                f"**Texture Recompression:** `{analysed_log['settings']['texture_recompression']}`",
            )
        )

        ryujinx_info = " | ".join(
            (
                f"**Version:** {analysed_log['emu_info']['ryu_version']}",
                f"**Firmware:** {analysed_log['emu_info']['ryu_firmware']}",
            )
        )

        log_embed = Embed(title=f"{cleaned_game_name}", colour=self.ryujinx_blue)
        log_embed.set_footer(text=f"Log uploaded by {author_name}")
        log_embed.add_field(
            name="General Info",
            value=" | ".join((ryujinx_info, hardware_info)),
            inline=False,
        )
        log_embed.add_field(
            name="System Settings",
            value=system_settings_info,
            inline=True,
        )
        log_embed.add_field(
            name="Graphics Settings",
            value=graphics_settings_info,
            inline=True,
        )
        if (
            cleaned_game_name == "Unknown"
            and analysed_log["game_info"]["errors"] == "No errors found in log"
        ):
            log_embed.add_field(
                name="Empty Log",
                value=f"""The log file appears to be empty. To get a proper log, follow these steps:
    1) In Logging settings, ensure `Enable Logging to File` is checked.
    2) Ensure the following default logs are enabled: `Info`, `Warning`, `Error`, `Guest` and `Stub`.
    3) Start a game up.
    4) Play until your issue occurs.
    5) Upload the latest log file which is larger than 3KB.""",
                inline=False,
            )
        if (
            cleaned_game_name == "Unknown"
            and analysed_log["game_info"]["errors"] != "No errors found in log"
        ):
            log_embed.add_field(
                name="Latest Error Snippet",
                value=analysed_log["game_info"]["errors"],
                inline=False,
            )
            log_embed.add_field(
                name="No Game Boot Detected",
                value=f"""No game boot has been detected in log file. To get a proper log, follow these steps:
    1) In Logging settings, ensure `Enable Logging to File` is checked.
    2) Ensure the following default logs are enabled: `Info`, `Warning`, `Error`, `Guest` and `Stub`.
    3) Start a game up.
    4) Play until your issue occurs.
    5) Upload the latest log file which is larger than 3KB.""",
                inline=False,
            )
        else:
            log_embed.add_field(
                name="Latest Error Snippet",
                value=analysed_log["game_info"]["errors"],
                inline=False,
            )
            log_embed.add_field(
                name="Mods", value=analysed_log["game_info"]["mods"], inline=False
            )
            log_embed.add_field(
                name="Cheats", value=analysed_log["game_info"]["cheats"], inline=False
            )

        log_embed.add_field(
            name="Notes",
            value=analysed_log["game_info"]["notes"],
            inline=False,
        )

        return log_embed

    async def log_file_read(self, message):
        attached_log = message.attachments[0]
        author_name = f"@{message.author.name}"
        log_file = await self.download_file(attached_log.url)

        if self.is_game_blocked(log_file):
            return await self.blocked_game_action(message)

        for role in message.author.roles:
            if role.id in self.disallowed_roles:
                embed = Embed(
                    colour=Colour(0xFF0000),
                    description="I'm not allowed to analyse this log.",
                )
                embed.set_footer(text=f"Log uploaded by {author_name}")
                return embed

        if not self.is_log_valid(log_file):
            embed = Embed(
                title="⚠️ Modified log detected ⚠️",
                colour=Colour(0xFCFC00),
                description="This log contains manually modified information and won't be analysed.",
            )
            embed.set_footer(text=f"Log uploaded by {author_name}")
            return embed

        try:
            analyser = LogAnalyser(log_file)
        except ValueError:
            return Embed(
                colour=self.ryujinx_blue,
                description="This log file appears to be invalid. Please make sure to upload a Ryujinx log file.",
            )

        is_channel_allowed = False
        for allowed_channel_id in self.bot.config.bot_log_allowed_channels.values():
            if message.channel.id == allowed_channel_id:
                is_channel_allowed = True
                break

        return self.format_analysed_log(
            author_name,
            analyser.analyse_discord(
                is_channel_allowed,
                self.bot.config.bot_log_allowed_channels["pr-testing"],
            ),
        )

    @commands.check(check_if_staff)
    @commands.command(
        aliases=["disallow_log_id", "forbid_log_id", "block_id", "blockid"]
    )
    async def disable_log_id(
        self, ctx: Context, disable_id: str, block_id_type: str, *, block_id: str
    ):
        match block_id_type.lower():
            case "app" | "app_id" | "appid" | "tid" | "title_id":
                if not is_app_id_valid(block_id):
                    return await ctx.send("The specified app id is invalid.")

                if add_disabled_app_id(self.bot, disable_id, block_id):
                    return await ctx.send(
                        f"Application id '{block_id}' is now blocked!"
                    )
                else:
                    return await ctx.send(
                        f"Application id '{block_id}' is already blocked."
                    )
            case "build" | "build_id" | "bid":
                if not is_build_id_valid(block_id):
                    return await ctx.send("The specified build id is invalid.")

                if add_disabled_build_id(self.bot, disable_id, block_id):
                    return await ctx.send(f"Build id '{block_id}' is now blocked!")
                else:
                    return await ctx.send(f"Build id '{block_id}' is already blocked.")
            case "ro_section" | "rosection":
                ro_section_snippet = block_id.strip("`").splitlines()
                ro_section_snippet = [
                    line for line in ro_section_snippet if len(line.strip()) > 0
                ]

                ro_section_info_regex = re.search(
                    r"PrintRoSectionInfo: main:", ro_section_snippet[0]
                )
                if ro_section_info_regex is None:
                    ro_section_snippet.insert(0, "PrintRoSectionInfo: main:")

                ro_section = LogAnalyser.get_main_ro_section(
                    "\n".join(ro_section_snippet)
                )
                if ro_section is not None and is_ro_section_valid(ro_section):
                    if add_disabled_ro_section(self.bot, disable_id, ro_section):
                        return await ctx.send(
                            f"The specified read-only section for '{disable_id}' is now blocked."
                        )
                    else:
                        return await ctx.send(
                            f"The specified read-only section for '{disable_id}' is already blocked."
                        )
            case _:
                return await ctx.send(
                    "The specified id type is invalid. Valid id types are: ['app_id', 'build_id', 'ro_section']"
                )

    @commands.check(check_if_staff)
    @commands.command(
        aliases=[
            "allow_log_id",
            "unblock_log_id",
            "unblock_id",
            "allow_id",
            "unblockid",
        ]
    )
    async def enable_log_id(self, ctx: Context, disable_id: str, block_id_type="all"):
        match block_id_type.lower():
            case "all":
                if remove_disable_id(self.bot, disable_id):
                    return await ctx.send(
                        f"All ids for '{disable_id}' are now unblocked!"
                    )
                else:
                    return await ctx.send(f"No blocked ids for '{disable_id}' found.")
            case "app" | "app_id" | "appid" | "tid" | "title_id":
                if remove_disabled_app_id(self.bot, disable_id):
                    return await ctx.send(
                        f"Application id for '{disable_id}' is now unblocked!"
                    )
                else:
                    return await ctx.send(
                        f"No blocked application id for '{disable_id}' found."
                    )
            case "build" | "build_id" | "bid":
                if remove_disabled_build_id(self.bot, disable_id):
                    return await ctx.send(
                        f"Build id for '{disable_id}' is now unblocked!"
                    )
                else:
                    return await ctx.send(f"No blocked build id '{disable_id}' found.")
            case "ro_section" | "rosection":
                if remove_disabled_ro_section(self.bot, disable_id):
                    return await ctx.send(
                        f"Read-only section for '{disable_id}' is now unblocked!"
                    )
                else:
                    return await ctx.send(
                        f"No blocked read-only section for '{disable_id}' found."
                    )
            case _:
                return await ctx.send(
                    "The specified id type is invalid. Valid id types are: ['all', 'app_id', 'build_id', 'ro_section']"
                )

    @commands.check(check_if_staff)
    @commands.command(
        aliases=[
            "disabled_ids",
            "blocked_ids",
            "listblockedids",
            "list_blocked_log_ids",
            "list_blocked_ids",
        ]
    )
    async def list_disabled_ids(self, ctx: Context):
        disabled_ids = get_disabled_ids(self.bot)
        id_types = {"app_id": "AppID", "build_id": "BID", "ro_section": "RoSection"}

        message = "**Blocking analysis of the following IDs:**\n"
        for name, entry in disabled_ids.items():
            message += f"- {name}:\n"
            for id_type, title in id_types.items():
                if len(entry[id_type]) > 0:
                    if id_type != "ro_section":
                        message += f"  - __{title}__: {entry[id_type]}\n"
                    else:
                        message += f"  - __{title}__\n"
            message += "\n"
        return await ctx.send(message)

    @commands.check(check_if_staff)
    @commands.command(
        aliases=[
            "get_blocked_ro_section",
            "disabled_ro_section",
            "blocked_ro_section",
            "list_disabled_ro_section",
            "list_blocked_ro_section",
        ]
    )
    async def get_disabled_ro_section(self, ctx: Context, disable_id: str):
        disabled_ids = get_disabled_ids(self.bot)
        disable_id = disable_id.lower()
        if (
            disable_id in disabled_ids.keys()
            and len(disabled_ids[disable_id]["ro_section"]) > 0
        ):
            message = f"**Blocked read-only section for '{disable_id}'**:\n"
            message += "```\n"
            for key, content in disabled_ids[disable_id]["ro_section"].items():
                match key:
                    case "module":
                        message += f"Module: {content}\n"
                    case "sdk_libraries":
                        message += f"SDK Libraries: \n"
                        for entry in content:
                            message += f"  SDK {entry}\n"
                message += "\n"
            message += "```"
            return await ctx.send(message)
        else:
            return await ctx.send(f"No read-only section blocked for '{disable_id}'.")

    async def analyse_log_message(self, message: Message, attachment_index=0):
        author_id = message.author.id
        author_mention = message.author.mention
        filename = message.attachments[attachment_index].filename
        filesize = message.attachments[attachment_index].size
        # Any message over 2000 chars is uploaded as message.txt, so this is accounted for
        log_file_link = message.jump_url

        uploaded_logs_exist = [
            True for elem in self.uploaded_log_info if filename in elem.values()
        ]
        if not any(uploaded_logs_exist):
            reply_message = await message.channel.send(
                "Log detected, parsing...", reference=message
            )
            try:
                embed = await self.log_file_read(message)
                if "Ryujinx_" in filename:
                    self.uploaded_log_info.append(
                        {
                            "filename": filename,
                            "file_size": filesize,
                            "link": log_file_link,
                            "author": author_id,
                        }
                    )
                    # Avoid duplicate log file analysis, at least temporarily; keep track of the last few filenames of uploaded logs
                    # this should help support channels not be flooded with too many log files
                    # fmt: off
                    self.uploaded_log_info = self.uploaded_log_info[-5:]
                    # fmt: on
                return await reply_message.edit(content=None, embed=embed)
            except UnicodeDecodeError as error:
                await reply_message.edit(
                    content=author_mention,
                    embed=Embed(
                        description="This log file appears to be invalid. Please re-check and re-upload your log file.",
                        colour=self.ryujinx_blue,
                    ),
                )
                logging.warning(error)
            except Exception as error:
                await reply_message.edit(
                    content=f"Error: Couldn't parse log; parser threw `{type(error).__name__}` exception."
                )
                logging.warning(error)
        else:
            duplicate_log_file = next(
                (
                    elem
                    for elem in self.uploaded_log_info
                    if elem["filename"] == filename
                    and elem["file_size"] == filesize
                    and elem["author"] == author_id
                ),
                None,
            )
            await message.channel.send(
                content=author_mention,
                embed=Embed(
                    description=f"The log file `{filename}` appears to be a duplicate [already uploaded here]({duplicate_log_file['link']}). Please upload a more recent file.",
                    colour=self.ryujinx_blue,
                ),
            )

    @commands.cooldown(3, 30, BucketType.channel)
    @commands.command(
        aliases=["analyselog", "analyse_log", "analyze", "analyzelog", "analyze_log"]
    )
    async def analyse(self, ctx: Context, attachment_number=1):
        await ctx.message.delete()
        if ctx.message.reference is not None:
            message = await ctx.fetch_message(ctx.message.reference.message_id)
            if len(message.attachments) >= attachment_number:
                attachment = message.attachments[attachment_number - 1]
                is_log_file, _ = self.is_valid_log_name(attachment)

                if is_log_file:
                    return await self.analyse_log_message(
                        message, attachment_number - 1
                    )
                else:
                    return await ctx.send(
                        f"The attached log file '{attachment.filename}' is not valid.",
                        reference=ctx.message.reference,
                    )

        return await ctx.send(
            "Please use `.analyse` as a reply to a message with an attached log file."
        )

    @Cog.listener()
    async def on_message(self, message: Message):
        await self.bot.wait_until_ready()
        if message.author.bot:
            return
        for attachment in message.attachments:
            is_log_file, is_ryujinx_log_file = self.is_valid_log_name(attachment)

            if is_log_file and not is_ryujinx_log_file:
                attached_log = message.attachments[0]
                log_file = await self.download_file(attached_log.url)
                # Large files show a header value when not downloaded completely
                # this regex makes sure that the log text to read starts from the first timestamp, ignoring headers
                log_file_header_regex = re.compile(
                    r"\d{2}:\d{2}:\d{2}\.\d{3}.*", re.DOTALL
                )
                log_file_match = re.search(log_file_header_regex, log_file)
                if log_file_match:
                    log_file = log_file_match.group(0)
                    if self.is_game_blocked(log_file):
                        return await message.channel.send(
                            content=None, embed=await self.blocked_game_action(message)
                        )
            elif (
                is_log_file
                and is_ryujinx_log_file
                and message.channel.id in self.bot_log_allowed_channels.values()
            ):
                return await self.analyse_log_message(
                    message, message.attachments.index(attachment)
                )
            elif (
                is_log_file
                and is_ryujinx_log_file
                and message.channel.id not in self.bot_log_allowed_channels.values()
            ):
                return await message.author.send(
                    content=message.author.mention,
                    embed=Embed(
                        description="\n".join(
                            (
                                f"Please upload Ryujinx log files to the correct location:\n",
                                f'<#{self.bot.config.bot_log_allowed_channels["windows-support"]}>: Windows help and troubleshooting',
                                f'<#{self.bot.config.bot_log_allowed_channels["linux-support"]}>: Linux help and troubleshooting',
                                f'<#{self.bot.config.bot_log_allowed_channels["macos-support"]}>: macOS help and troubleshooting',
                                f'<#{self.bot.config.bot_log_allowed_channels["patreon-support"]}>: Help and troubleshooting for Patreon subscribers',
                                f'<#{self.bot.config.bot_log_allowed_channels["development"]}>: Ryujinx development discussion',
                                f'<#{self.bot.config.bot_log_allowed_channels["pr-testing"]}>: Discussion of in-progress pull request builds',
                            )
                        ),
                        colour=self.ryujinx_blue,
                    ),
                )


async def setup(bot):
    await bot.add_cog(LogFileReader(bot))
