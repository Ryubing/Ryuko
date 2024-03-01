import json
import math
import os

from robocop_ng.helpers.data_loader import read_json


def get_crontab_path(bot):
    return os.path.join(bot.state_dir, "data/robocronptab.json")


def get_crontab(bot):
    return read_json(bot, get_crontab_path(bot))


def set_crontab(bot, contents):
    with open(get_crontab_path(bot), "w") as f:
        f.write(contents)


def add_job(bot, job_type, job_name, job_details, timestamp):
    timestamp = str(math.floor(timestamp))
    job_name = str(job_name)
    ctab = get_crontab(bot)

    if job_type not in ctab:
        ctab[job_type] = {}

    if timestamp not in ctab[job_type]:
        ctab[job_type][timestamp] = {}

    ctab[job_type][timestamp][job_name] = job_details
    set_crontab(bot, json.dumps(ctab))


def delete_job(bot, timestamp, job_type, job_name):
    timestamp = str(timestamp)
    job_name = str(job_name)
    ctab = get_crontab(bot)

    del ctab[job_type][timestamp][job_name]

    set_crontab(bot, json.dumps(ctab))
