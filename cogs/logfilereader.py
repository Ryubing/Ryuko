from inspect import Traceback
import logging
import discord
from discord.ext.commands import Cog
import re
import aiohttp
import config

logging.basicConfig(
    format="%(asctime)s (%(levelname)s) %(message)s (Line %(lineno)d)",
    level=logging.DEBUG,
)


class LogFileReader(Cog):
    def __init__(self, bot):
        self.bot = bot
        # Allows log analysis in #support and #patreon-support channels respectively
        self.bot_log_allowed_channels = config.bot_log_allowed_channels
        self.uploaded_log_filenames = []

    async def download_file(self, log_url):
        async with aiohttp.ClientSession() as session:
            # Grabs first and last few bytes of log file to prevent abuse from large files
            headers = {"Range": "bytes=0-20000, -6000"}
            async with session.get(log_url, headers=headers) as response:
                return await response.text("UTF-8")

    async def log_file_read(self, message):
        attached_log = message.attachments[0]
        author = f"@{message.author.name}"
        log_file = await self.download_file(attached_log.url)
        # Large files show a header value when not downloaded completely
        # this regex makes sure that the log text to read starts from the first timestamp, ignoring headers
        log_file_header_regex = re.compile(r"\d{2}:\d{2}:\d{2}\.\d{3}.*", re.DOTALL)
        log_file = re.search(log_file_header_regex, log_file).group(0)

        regex_map = {
            "Ryu_Version": "Ryujinx Version",
            "Firmware": "Firmware Version",
            "OS": "Operating System",
            "CPU": "CPU",
            "GPU": "PrintGpuInformation",
            "RAM": "RAM",
            "Game_Name": "Loader LoadNca: Application Loaded",
            "Logs_Enabled": "Logs Enabled",
        }

        def make_regex_obj(key, value):
            # Since RAM values in log are structured as "RAM: Total 16297 MB ;", regex tries to account for the unneeded 'Total' string
            return re.compile(fr"{value}:(\sTotal)?\s(?P<{key}>[^;\r]*)", re.MULTILINE)

        def find_specs(body, key, regexobj):
            match = regexobj.search(body)
            return match.group(key).rstrip() if match is not None else "Unknown"

        def specs_search(body):
            return {
                key: find_specs(body, key, make_regex_obj(key, value))
                for key, value in regex_map.items()
            }

        def mods_information(log_file):
            mods_regex = re.compile(r"Found mod\s\'(.+?)\'\s(\[.+?\])")
            matches = re.findall(mods_regex, log_file)
            if matches:
                mods = [{"mod": match[0], "status": match[1]} for match in matches]
                mods_status = [
                    f"ℹ️ {i['mod']} ({'ExeFS' if i['status'] == '[E]' else 'RomFS'})"
                    for i in mods
                ]
                return mods_status

        def generate_log_embed(author_id, log_info):
            embed = {
                "hardware_info": {
                    "cpu": "Unknown",
                    "gpu": "Unknown",
                    "ram": "Unknown",
                    "os": "Unknown",
                },
                "emu_info": {"ryu_version": "Unknown", "ryu_firmware": "Unknown"},
                "game_info": {
                    "game_name": "Unknown",
                    "errors": "No errors found in log",
                    "mods": "No mods found",
                    "notes": [],
                },
            }

            def find_error_message(log_file):
                try:
                    errors = []
                    curr_error_lines = []
                    for line in log_file.splitlines():
                        if line == "":
                            continue
                        if "|E|" in line:
                            curr_error_lines = [line]
                            errors.append(curr_error_lines)
                        elif line[0] == " " or line == "":
                            curr_error_lines.append(line)
                    last_errors = "\n".join(
                        errors[-1][:2] if "|E|" in errors[-1][0] else ""
                    )
                except IndexError:
                    last_errors = None
                return last_errors

            # Finds the lastest error denoted by |E| in the log and its first line
            error_message = find_error_message(log_file)
            if error_message:
                embed["game_info"]["errors"] = f"```{error_message}```"
            else:
                pass

            # Find information on installed mods
            game_mods = mods_information(log_file)
            if game_mods:
                embed["game_info"]["mods"] = "\n".join(game_mods)
            else:
                pass

            controllers_regex = re.compile(r"Hid Configure: ([^\r\n]+)")
            controllers = re.findall(controllers_regex, log_file)
            if controllers:
                input_status = [f"ℹ {match}" for match in controllers]
                input_string = "\n".join(input_status)
            else:
                input_string = "⚠️ No controller information found"
            embed["game_info"]["notes"].append(input_string)

            try:
                ram_avaliable_regex = re.compile(r"Available\s(\d+)(?=\sMB)")
                ram_avaliable = re.search(ram_avaliable_regex, log_file)[1]
                if int(ram_avaliable) < 8000:
                    ram_warning = "⚠️ Less than 8GB RAM avaliable"
                    embed["game_info"]["notes"].append(ram_warning)
            except TypeError:
                pass

            if "Darwin" in log_info["OS"]:
                mac_os_warning = "**❌ macOS is currently unsupported**"
                embed["game_info"]["notes"].append(mac_os_warning)

            if "Intel" in log_info["GPU"]:
                if "Darwin" in log_info["OS"] or "Windows" in log_info["OS"]:
                    intel_gpu_warning = "**⚠️ Intel iGPUs are known to have driver issues, consider using a discrete GPU**"
                    embed["game_info"]["notes"].append(intel_gpu_warning)

            # Find information on logs, whether defaults are enabled or not
            default_logs = ["Info", "Warning", "Error", "Guest", "Stub"]
            user_logs = log_info["Logs_Enabled"].rstrip().replace(" ", "").split(",")
            disabled_logs = set(default_logs).difference(set(user_logs))
            if disabled_logs:
                logs_status = [f"⚠️ {log} log is not enabled" for log in disabled_logs]
                log_string = "\n".join(logs_status)
            else:
                log_string = "✅ Default logs enabled"
            embed["game_info"]["notes"].append(log_string)

            embed["hardware_info"]["cpu"] = log_info["CPU"]
            embed["hardware_info"]["gpu"] = log_info["GPU"]
            embed["hardware_info"]["ram"] = log_info["RAM"]
            embed["hardware_info"]["os"] = log_info["OS"]
            embed["emu_info"]["ryu_version"] = log_info["Ryu_Version"]
            embed["emu_info"]["ryu_firmware"] = log_info["Firmware"]

            cleaned_game_name = re.sub(r"\s\[(64|32)-bit\]$", "", log_info["Game_Name"])
            embed["game_info"]["game_name"] = cleaned_game_name

            hardware_info = "\n".join(
                (
                    f"**CPU:** {embed['hardware_info']['cpu']}",
                    f"**GPU:** {embed['hardware_info']['gpu']}",
                    f"**RAM:** {embed['hardware_info']['ram']}",
                    f"**OS:** {embed['hardware_info']['os']}",
                )
            )

            ryujinx_info = "\n".join(
                (
                    f"**Version:** {embed['emu_info']['ryu_version']}",
                    f"**Firmware:** {embed['emu_info']['ryu_firmware']}",
                )
            )

            log_embed = discord.Embed(
                title=f"{cleaned_game_name}", colour=discord.Colour(0x4A90E2)
            )
            log_embed.set_footer(text=f"Log uploaded by {author_id}")
            log_embed.add_field(name="Hardware Info", value=hardware_info)
            log_embed.add_field(name="Ryujinx Info", value=ryujinx_info)
            if log_info["Game_Name"] == "Unknown":
                log_embed.add_field(
                    name="Empty Log",
                    value="""This log file appears to be empty. To get a proper log, follow these steps:
                    \n 1) Start a game up.
                    \n 2) Play until your issue occurs.
                    \n 3) Upload your log file.""",
                    inline=False,
                )
            log_embed.add_field(
                name="Latest Error Snippet",
                value=embed["game_info"]["errors"],
                inline=False,
            )
            log_embed.add_field(
                name="Mods", value=embed["game_info"]["mods"], inline=False
            )
            log_embed.add_field(
                name="Notes",
                value="\n".join([note for note in embed["game_info"]["notes"]]),
                inline=False,
            )

            return log_embed

        system_info = specs_search(log_file)
        return generate_log_embed(author, system_info)

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if message.author.bot:
            return

        # If message has an attachment
        try:
            author = message.author.mention
            filename = message.attachments[0].filename
            # Any message over 2000 chars is uploaded as message.txt, so this is accounted for
            log_file_regex = re.compile(r"^Ryujinx_.*\.log|message\.txt$")
            is_log_file = re.match(log_file_regex, filename)
            if message.channel.id in self.bot_log_allowed_channels and is_log_file:
                if filename not in self.uploaded_log_filenames:
                    reply_message = await message.channel.send(
                        "Log detected, parsing..."
                    )
                    try:
                        embed = await self.log_file_read(message)
                        if "Ryujinx_" in filename:
                            self.uploaded_log_filenames.append(filename)
                            # Avoid duplicate log file analysis, at least temporarily; keep track of the last few filenames of uploaded logs
                            # this should help support channels not be flooded with too many log files
                            self.uploaded_log_filenames = self.uploaded_log_filenames[
                                -5:
                            ]
                        return await reply_message.edit(content=None, embed=embed)
                    except UnicodeDecodeError:
                        return await message.channel.send(
                            f"This log file appears to be invalid {author}. Please re-check and re-upload your log file."
                        )
                    except Exception as error:
                        await reply_message.edit(
                            content=f"Error: Couldn't parse log; parser threw {type(error).__name__} exception."
                        )
                        print(logging.warn(error))
                else:
                    await message.channel.send(
                        f"The log file `{filename}` appears to be a duplicate {author}. Please upload a more recent file."
                    )
            elif not is_log_file:
                return await message.channel.send(
                    f"{author} Your file does not match the Ryujinx log format. Please check your file."
                )
            else:
                return await message.channel.send(
                    f"{author} Please upload log files to {' or '.join([f'<#{id}>' for id in self.bot_log_allowed_channels])}"
                )
        except IndexError:
            pass


def setup(bot):
    bot.add_cog(LogFileReader(bot))
