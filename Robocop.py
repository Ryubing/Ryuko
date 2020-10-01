import os
import sys
import logging
import logging.handlers
import traceback
import aiohttp
import config

import discord
from discord.ext import commands

script_name = os.path.basename(__file__).split(".")[0]

log_file_name = f"{script_name}.log"

# Limit of discord (non-nitro) is 8MB (not MiB)
max_file_size = 1000 * 1000 * 8
backup_count = 3
file_handler = logging.handlers.RotatingFileHandler(
    filename=log_file_name, maxBytes=max_file_size, backupCount=backup_count
)
stdout_handler = logging.StreamHandler(sys.stdout)

log_format = logging.Formatter(
    "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
)
file_handler.setFormatter(log_format)
stdout_handler.setFormatter(log_format)

log = logging.getLogger("discord")
log.setLevel(logging.INFO)
log.addHandler(file_handler)
log.addHandler(stdout_handler)


def get_prefix(bot, message):
    prefixes = config.prefixes

    return commands.when_mentioned_or(*prefixes)(bot, message)


wanted_jsons = [
    "data/restrictions.json",
    "data/robocronptab.json",
    "data/userlog.json",
    "data/invites.json",
]

intents = discord.Intents.default()
intents.typing = False
intents.members = True

bot = commands.Bot(command_prefix=get_prefix, description=config.bot_description, intents=intents)
bot.help_command = commands.DefaultHelpCommand(dm_help=True)

bot.log = log
bot.config = config
bot.script_name = script_name
bot.wanted_jsons = wanted_jsons

if __name__ == "__main__":
    for cog in config.initial_cogs:
        try:
            bot.load_extension(cog)
        except:
            log.error(f"Failed to load cog {cog}.")
            log.error(traceback.print_exc())


@bot.event
async def on_ready():
    aioh = {"User-Agent": f"{script_name}/1.0'"}
    bot.aiosession = aiohttp.ClientSession(headers=aioh)
    bot.app_info = await bot.application_info()
    bot.botlog_channel = bot.get_channel(config.botlog_channel)

    log.info(
        f"\nLogged in as: {bot.user.name} - "
        f"{bot.user.id}\ndpy version: {discord.__version__}\n"
    )
    game_name = f"{config.prefixes[0]}help"

    # Send "Robocop has started! x has y members!"
    guild = bot.botlog_channel.guild
    msg = (
        f"{bot.user.name} has started! "
        f"{guild.name} has {guild.member_count} members!"
    )

    data_files = [discord.File(fpath) for fpath in wanted_jsons]
    await bot.botlog_channel.send(msg, files=data_files)

    activity = discord.Activity(name=game_name, type=discord.ActivityType.listening)

    await bot.change_presence(activity=activity)


@bot.event
async def on_command(ctx):
    log_text = (
        f"{ctx.message.author} ({ctx.message.author.id}): " f'"{ctx.message.content}" '
    )
    if ctx.guild:  # was too long for tertiary if
        log_text += (
            f'on "{ctx.channel.name}" ({ctx.channel.id}) '
            f'at "{ctx.guild.name}" ({ctx.guild.id})'
        )
    else:
        log_text += f"on DMs ({ctx.channel.id})"
    log.info(log_text)


@bot.event
async def on_error(event_method, *args, **kwargs):
    log.error(f"Error on {event_method}: {sys.exc_info()}")


@bot.event
async def on_command_error(ctx, error):
    error_text = str(error)

    err_msg = (
        f'Error with "{ctx.message.content}" from '
        f'"{ctx.message.author} ({ctx.message.author.id}) '
        f"of type {type(error)}: {error_text}"
    )

    log.error(err_msg)

    if not isinstance(error, commands.CommandNotFound):
        err_msg = bot.escape_message(err_msg)
        await bot.botlog_channel.send(err_msg)

    if isinstance(error, commands.NoPrivateMessage):
        return await ctx.send("This command doesn't work on DMs.")
    elif isinstance(error, commands.MissingPermissions):
        roles_needed = "\n- ".join(error.missing_perms)
        return await ctx.send(
            f"{ctx.author.mention}: You don't have the right"
            " permissions to run this command. You need: "
            f"```- {roles_needed}```"
        )
    elif isinstance(error, commands.BotMissingPermissions):
        roles_needed = "\n-".join(error.missing_perms)
        return await ctx.send(
            f"{ctx.author.mention}: Bot doesn't have "
            "the right permissions to run this command. "
            "Please add the following roles: "
            f"```- {roles_needed}```"
        )
    elif isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(
            f"{ctx.author.mention}: You're being "
            "ratelimited. Try in "
            f"{error.retry_after:.1f} seconds."
        )
    elif isinstance(error, commands.CheckFailure):
        return await ctx.send(
            f"{ctx.author.mention}: Check failed. "
            "You might not have the right permissions "
            "to run this command, or you may not be able "
            "to run this command in the current channel."
        )
    elif isinstance(error, commands.CommandInvokeError) and (
        "Cannot send messages to this user" in error_text
    ):
        return await ctx.send(
            f"{ctx.author.mention}: I can't DM you.\n"
            "You might have me blocked or have DMs "
            f"blocked globally or for {ctx.guild.name}.\n"
            "Please resolve that, then "
            "run the command again."
        )
    elif isinstance(error, commands.CommandNotFound):
        # Nothing to do when command is not found.
        return

    help_text = (
        f"Usage of this command is: ```{ctx.prefix}{ctx.command.name} "
        f"{ctx.command.signature}```\nPlease see `{ctx.prefix}help "
        f"{ctx.command.name}` for more info about this command."
    )

    # Keep a list of commands that involve mentioning users
    # and can involve users leaving/getting banned
    ಠ_ಠ = ["warn", "kick", "ban"]

    if isinstance(error, commands.BadArgument):
        # and if said commands get used, add a specific notice.
        if ctx.command.name in ಠ_ಠ:
            help_text = (
                "This probably means that user left (or already got kicked/banned).\n"
                + help_text
            )

        return await ctx.send(
            f"{ctx.author.mention}: You gave incorrect arguments. {help_text}"
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(
            f"{ctx.author.mention}: You gave incomplete arguments. {help_text}"
        )


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if (message.guild) and (message.guild.id not in config.guild_whitelist):
        return

    # Ignore messages in newcomers channel, unless it's potentially
    # an allowed command
    welcome_allowed = ["reset", "kick", "ban", "warn"]
    if message.channel.id == config.welcome_channel and not any(
        cmd in message.content for cmd in welcome_allowed
    ):
        return

    ctx = await bot.get_context(message)
    await bot.invoke(ctx)


if not os.path.exists("data"):
    os.makedirs("data")

for wanted_json in wanted_jsons:
    if not os.path.exists(wanted_json):
        with open(wanted_json, "w") as f:
            f.write("{}")

bot.run(config.token, bot=True, reconnect=True)
