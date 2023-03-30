from discord import RawMemberRemoveEvent, Member
from discord.ext.commands import Cog

from robocop_ng.helpers.roles import add_user_roles, get_user_roles


class RolePersistence(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_raw_member_remove(self, payload: RawMemberRemoveEvent):
        save_roles = []
        for role in payload.user.roles:
            if role.is_assignable() and \
                    not role.is_default() and not role.is_premium_subscriber() and \
                    not role.is_bot_managed() and not role.is_integration():
                save_roles.append(role.id)

        if len(save_roles) > 0:
            add_user_roles(payload.user.id, save_roles)

    @Cog.listener()
    async def on_member_join(self, member: Member):
        user_roles = get_user_roles(member.id)
        if len(user_roles) > 0:
            user_roles = [member.guild.get_role(int(role)) for role in user_roles
                          if member.guild.get_role(int(role)) is not None]
            await member.add_roles(*user_roles, reason="Restoring old roles from `role_persistence`.")
