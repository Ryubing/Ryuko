import json
import os
from typing import Union

from robocop_ng.helpers.data_loader import read_json


def get_invites_path(bot):
    return os.path.join(bot.state_dir, "data/invites.json")


def get_invites(bot) -> dict[str, dict[str, Union[str, int]]]:
    return read_json(bot, get_invites_path(bot))


def add_invite(bot, invite_id: str, url: str, max_uses: int, code: str):
    invites = get_invites(bot)
    invites[invite_id] = {
        "uses": 0,
        "url": url,
        "max_uses": max_uses,
        code: code,
    }
    set_invites(bot, invites)


def set_invites(bot, contents: dict[str, dict[str, Union[str, int]]]):
    with open(get_invites_path(bot), "w") as f:
        json.dump(contents, f)
