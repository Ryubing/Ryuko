import discord
import re
import aiohttp


class LogFileReader:
    def __init__(self, bot):
        self.bot = bot

    async def download_file(log_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(log_url) as response:
                return await response.text()

    async def log_file_read(message):
        attached_log = message.attachments[0]
        filename = attached_log.filename
        if re.match(r"^Ryujinx_.*\.log$", filename):
            author = f"@{message.author.name}"
            log_file = await LogFileReader.download_file(attached_log.url)

            regex_map = {
                "Ryu_Version": "Ryujinx Version",
                "Firmware": "Firmware Version",
                "OS": "Operating System",
                "CPU": "CPU",
                "GPU": "PrintGpuInformation",
                "RAM": "Total RAM",
                "Game_Name": "Loader LoadNca: Application Loaded",
            }

            def make_regex_obj(key, value):
                return re.compile(fr"{value}: (?P<{key}>.*)$", re.MULTILINE)

            def find_specs(body, key, regexobj):
                match = regexobj.search(body)
                return match.group(key) if match is not None else None

            def specs_search(body):
                return {
                    key: find_specs(body, key, make_regex_obj(key, value))
                    for key, value in regex_map.items()
                }

            system_info = specs_search(log_file)

            def generate_log_embed(author_id, log_info):
                log_embed = discord.Embed(
                    title=f"{log_info['Game_Name']}", colour=discord.Colour(0x4a90e2)
                )
                log_embed.set_footer(text=f"Log uploaded by {author_id}")
                log_embed.add_field(
                    name="**Ryujinx Info**",
                    value=f"**Version:** {log_info['Ryu_Version']}\n**Firmware:** {log_info['Firmware']}",
                )
                log_embed.add_field(
                    name="Hardware Info",
                    value=f"**CPU:** {log_info['CPU']}\n**GPU:** {log_info['GPU']}\n**RAM:** {log_info['RAM']}",
                )
                return log_embed

            print(system_info)
            # message = f"This is a valid Ryujinx log file. Thanks <@{author}>"
            return generate_log_embed(author, system_info)
