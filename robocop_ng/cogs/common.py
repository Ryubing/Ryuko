import asyncio
import traceback
import datetime
import humanize
import time
import math
import parsedatetime
from discord.ext.commands import Cog


class Common(Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.async_call_shell = self.async_call_shell
        self.bot.slice_message = self.slice_message
        self.max_split_length = 3
        self.bot.hex_to_int = self.hex_to_int
        self.bot.download_file = self.download_file
        self.bot.aiojson = self.aiojson
        self.bot.aioget = self.aioget
        self.bot.aiogetbytes = self.aiogetbytes
        self.bot.get_relative_timestamp = self.get_relative_timestamp
        self.bot.escape_message = self.escape_message
        self.bot.parse_time = self.parse_time
        self.bot.haste = self.haste

    def parse_time(self, delta_str):
        cal = parsedatetime.Calendar()
        time_struct, parse_status = cal.parse(delta_str)
        res_timestamp = math.floor(time.mktime(time_struct))
        return res_timestamp

    def get_relative_timestamp(
        self,
        time_from=None,
        time_to=None,
        humanized=False,
        include_from=False,
        include_to=False,
    ):
        # Setting default value to utcnow() makes it show time from cog load
        # which is not what we want
        if not time_from:
            time_from = datetime.datetime.utcnow()
        if not time_to:
            time_to = datetime.datetime.utcnow()
        if humanized:
            humanized_string = humanize.naturaltime(time_from - time_to)
            if include_from and include_to:
                str_with_from_and_to = (
                    f"{humanized_string} "
                    f"({str(time_from).split('.')[0]} "
                    f"- {str(time_to).split('.')[0]})"
                )
                return str_with_from_and_to
            elif include_from:
                str_with_from = (
                    f"{humanized_string} " f"({str(time_from).split('.')[0]})"
                )
                return str_with_from
            elif include_to:
                str_with_to = f"{humanized_string} " f"({str(time_to).split('.')[0]})"
                return str_with_to
            return humanized_string
        else:
            epoch = datetime.datetime.utcfromtimestamp(0)
            epoch_from = (time_from - epoch).total_seconds()
            epoch_to = (time_to - epoch).total_seconds()
            second_diff = epoch_to - epoch_from
            result_string = str(datetime.timedelta(seconds=second_diff)).split(".")[0]
            return result_string

    async def aioget(self, url):
        try:
            data = await self.bot.aiosession.get(url)
            if data.status == 200:
                text_data = await data.text()
                self.bot.log.info(f"Data from {url}: {text_data}")
                return text_data
            else:
                self.bot.log.error(f"HTTP Error {data.status} while getting {url}")
        except:
            self.bot.log.error(
                f"Error while getting {url} "
                f"on aiogetbytes: {traceback.format_exc()}"
            )

    async def aiogetbytes(self, url):
        try:
            data = await self.bot.aiosession.get(url)
            if data.status == 200:
                byte_data = await data.read()
                self.bot.log.debug(f"Data from {url}: {byte_data}")
                return byte_data
            else:
                self.bot.log.error(f"HTTP Error {data.status} while getting {url}")
        except:
            self.bot.log.error(
                f"Error while getting {url} "
                f"on aiogetbytes: {traceback.format_exc()}"
            )

    async def aiojson(self, url):
        try:
            data = await self.bot.aiosession.get(url)
            if data.status == 200:
                text_data = await data.text()
                self.bot.log.info(f"Data from {url}: {text_data}")
                content_type = data.headers["Content-Type"]
                return await data.json(content_type=content_type)
            else:
                self.bot.log.error(f"HTTP Error {data.status} while getting {url}")
        except:
            self.bot.log.error(
                f"Error while getting {url} "
                f"on aiogetbytes: {traceback.format_exc()}"
            )

    def hex_to_int(self, color_hex: str):
        """Turns a given hex color into an integer"""
        return int("0x" + color_hex.strip("#"), 16)

    def escape_message(self, text: str):
        """Escapes unfun stuff from messages"""
        return str(text).replace("@", "@ ").replace("<#", "# ").replace("_", "\_")

    # This function is based on https://stackoverflow.com/a/35435419/3286892
    # by link2110 (https://stackoverflow.com/users/5890923/link2110)
    # modified by Ave (https://github.com/aveao), licensed CC-BY-SA 3.0
    async def download_file(self, url, local_filename):
        file_resp = await self.bot.aiosession.get(url)
        file = await file_resp.read()
        with open(local_filename, "wb") as f:
            f.write(file)

    # 2000 is maximum limit of discord
    async def slice_message(self, text, size=2000, prefix="", suffix=""):
        """Slices a message into multiple messages"""
        if len(text) > size * self.max_split_length:
            haste_url = await self.haste(text)
            return [
                f"Message is too long ({len(text)} > "
                f"{size * self.max_split_length} "
                f"({size} * {self.max_split_length}))"
                f", go to haste: <{haste_url}>"
            ]
        reply_list = []
        size_wo_fix = size - len(prefix) - len(suffix)
        while len(text) > size_wo_fix:
            reply_list.append(f"{prefix}{text[:size_wo_fix]}{suffix}")
            text = text[size_wo_fix:]
        reply_list.append(f"{prefix}{text}{suffix}")
        return reply_list

    async def haste(self, text, instance="https://mystb.in/"):
        response = await self.bot.aiosession.post(f"{instance}documents", data=text)
        if response.status == 200:
            result_json = await response.json()
            return f"{instance}{result_json['key']}"
        else:
            return f"Error {response.status}: {response.text}"

    async def async_call_shell(
        self, shell_command: str, inc_stdout=True, inc_stderr=True
    ):
        pipe = asyncio.subprocess.PIPE
        proc = await asyncio.create_subprocess_shell(
            str(shell_command), stdout=pipe, stderr=pipe
        )

        if not (inc_stdout or inc_stderr):
            return "??? you set both stdout and stderr to False????"

        proc_result = await proc.communicate()
        stdout_str = proc_result[0].decode("utf-8").strip()
        stderr_str = proc_result[1].decode("utf-8").strip()

        if inc_stdout and not inc_stderr:
            return stdout_str
        elif inc_stderr and not inc_stdout:
            return stderr_str

        if stdout_str and stderr_str:
            return f"stdout:\n\n{stdout_str}\n\n" f"======\n\nstderr:\n\n{stderr_str}"
        elif stdout_str:
            return f"stdout:\n\n{stdout_str}"
        elif stderr_str:
            return f"stderr:\n\n{stderr_str}"

        return "No output."


async def setup(bot):
    await bot.add_cog(Common(bot))
