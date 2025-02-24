from robocop_ng import config


def check_if_staff(ctx):
    if not ctx.guild:
        return False
    return any(r.id in config.staff_role_ids for r in ctx.author.roles)


def check_if_bot_manager(ctx):
    if not ctx.guild:
        return False
    return any(r.id == config.bot_manager_role_id for r in ctx.author.roles)


def check_if_staff_or_ot(ctx):
    if not ctx.guild:
        return True
    is_ot = ctx.channel.name == "general"
    is_bot_cmds = ctx.channel.name == "bot-spam"
    is_staff = any(r.id in config.staff_role_ids for r in ctx.author.roles)
    return is_ot or is_staff or is_bot_cmds


def check_if_staff_or_dm(ctx):
    if not ctx.guild:
        return True
    return any(r.id in config.staff_role_ids for r in ctx.author.roles)


def check_if_collaborator(ctx):
    if not ctx.guild:
        return False
    return any(
        r.id in config.staff_role_ids + config.allowed_pin_roles
        for r in ctx.author.roles
    )


def check_if_pin_channel(ctx):
    if not ctx.guild:
        return False
    return ctx.message.channel.id in config.allowed_pin_channels
