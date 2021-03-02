import discord
import re
import aiohttp


class LogFileReader:
    def __init__(self, bot):
        self.bot = bot

    async def download_file(self, log_url):
        async with aiohttp.ClientSession() as session:
            # grabs first and last 4kB of log file to prevent abuse from large files
            headers = {"Range": "bytes=0-6000, -6000"}
            async with session.get(log_url, headers=headers) as response:
                return await response.text()

    async def log_file_read(self, message):
        attached_log = message.attachments[0]
        filename = attached_log.filename
        if re.match(r"^Ryujinx_.*\.log$", filename):
            author = f"@{message.author.name}"
            log_file = await self.download_file(attached_log.url)

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
                # since RAM values in log are structured as "RAM: Total 16297 MB ;", regex tries to account for the unneeded 'Total' string
                return re.compile(
                    fr"{value}:(\sTotal)?\s(?P<{key}>[^;\r]*)", re.MULTILINE
                )

            def find_specs(body, key, regexobj):
                match = regexobj.search(body)
                return match.group(key).rstrip() if match is not None else "Unknown"

            def specs_search(body):
                return {
                    key: find_specs(body, key, make_regex_obj(key, value))
                    for key, value in regex_map.items()
                }

            system_info = specs_search(log_file)

            def generate_log_embed(author_id, log_info):
                log_embed = discord.Embed(
                    title=f"{log_info['Game_Name']}", colour=discord.Colour(0x4A90E2)
                )
                log_embed.set_footer(text=f"Log uploaded by {author_id}")
                log_embed.add_field(
                    name="Ryujinx Info",
                    value=f"**Version:** {log_info['Ryu_Version']}\n**Firmware:** {log_info['Firmware']}",
                )
                log_embed.add_field(
                    name="Hardware Info",
                    value=f"**CPU:** {log_info['CPU']}\n**GPU:** {log_info['GPU']}\n**RAM:** {log_info['RAM']}\n**OS:** {log_info['OS']}",
                )
                if log_info["Game_Name"] == "Unknown":
                    log_embed.add_field(
                        name="Empty Log",
                        value=f"This log file appears to be empty. To get a proper log, follow these steps:\n 1) Start a game up.\n 2) Play until your issue occurs.\n 3) Upload your log file.",
                        inline=False,
                    )
                default_logs = ["Info", "Warning", "Error", "Guest", "Stub"]
                user_logs = (
                    log_info["Logs_Enabled"].rstrip().replace(" ", "").split(",")
                )
                disabled_logs = set(default_logs).difference(set(user_logs))
                if disabled_logs:
                    logs_warning = [
                        f":warning: {log} log is not enabled." for log in disabled_logs
                    ]
                    log_embed.add_field(
                        name="Notes", value="\n".join(logs_warning), inline=False
                    )
                return log_embed

            return generate_log_embed(author, system_info)
