import json
import os
import time

from robocop_ng.helpers.data_loader import read_json

userlog_event_types = {
    "warns": "Warn",
    "bans": "Ban",
    "kicks": "Kick",
    "mutes": "Mute",
    "notes": "Note",
}


def get_userlog_path(bot):
    return os.path.join(bot.state_dir, "data/userlog.json")


def get_userlog(bot):
    return read_json(bot, get_userlog_path(bot))


def set_userlog(bot, contents):
    with open(get_userlog_path(bot), "w") as f:
        f.write(contents)


def fill_userlog(bot, userid, uname):
    userlogs = get_userlog(bot)
    uid = str(userid)
    if uid not in userlogs:
        userlogs[uid] = {
            "warns": [],
            "mutes": [],
            "kicks": [],
            "bans": [],
            "notes": [],
            "watch": False,
            "name": "n/a",
        }
    if uname:
        userlogs[uid]["name"] = uname

    return userlogs, uid


def userlog(bot, uid, issuer, reason, event_type, uname: str = ""):
    userlogs, uid = fill_userlog(bot, uid, uname)

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_data = {
        "issuer_id": issuer.id,
        "issuer_name": f"{issuer}",
        "reason": reason,
        "timestamp": timestamp,
    }
    if event_type not in userlogs[uid]:
        userlogs[uid][event_type] = []
    userlogs[uid][event_type].append(log_data)
    set_userlog(bot, json.dumps(userlogs))
    return len(userlogs[uid][event_type])


def setwatch(bot, uid, issuer, watch_state, uname: str = ""):
    userlogs, uid = fill_userlog(bot, uid, uname)

    userlogs[uid]["watch"] = watch_state
    set_userlog(bot, json.dumps(userlogs))
    return
