import json
import os


def get_disabled_ids_path(bot) -> str:
    old_filepath = os.path.join(bot.state_dir, "data/disabled_tids.json")
    new_filepath = os.path.join(bot.state_dir, "data/disabled_ids.json")
    if os.path.isfile(old_filepath):
        os.rename(old_filepath, new_filepath)
    return new_filepath


def is_app_id_valid(app_id: str) -> bool:
    return len(app_id) == 16 and app_id.isalnum()


def is_build_id_valid(build_id: str) -> bool:
    return 32 <= len(build_id) <= 64 and build_id.isalnum()


def get_disabled_ids(bot) -> dict[str, dict[str, str]]:
    if os.path.isfile(get_disabled_ids_path(bot)):
        with open(get_disabled_ids_path(bot), "r") as f:
            disabled_ids = json.load(f)
        # Migration code
        if "app_id" not in disabled_ids.keys():
            disabled_ids = {"app_id": disabled_ids, "build_id": {}}
        return disabled_ids

    return {"app_id": {}, "build_id": {}}


def set_disabled_ids(bot, contents: dict[str, dict[str, str]]):
    with open(get_disabled_ids_path(bot), "w") as f:
        json.dump(contents, f)


def is_app_id_disabled(bot, app_id: str) -> bool:
    disabled_ids = get_disabled_ids(bot)
    app_id = app_id.lower()
    return app_id in disabled_ids["app_id"].keys()


def is_build_id_disabled(bot, build_id: str) -> bool:
    disabled_ids = get_disabled_ids(bot)
    build_id = build_id.lower()
    if len(build_id) < 64:
        build_id += "0" * (64 - len(build_id))
    return build_id in disabled_ids["build_id"].keys()


def add_disabled_app_id(bot, app_id: str, note="") -> bool:
    disabled_ids = get_disabled_ids(bot)
    app_id = app_id.lower()
    if app_id not in disabled_ids["app_id"].keys():
        disabled_ids["app_id"][app_id] = note
        set_disabled_ids(bot, disabled_ids)
        return True
    return False


def remove_disabled_app_id(bot, app_id: str) -> bool:
    disabled_ids = get_disabled_ids(bot)
    app_id = app_id.lower()
    if app_id in disabled_ids["app_id"].keys():
        del disabled_ids["app_id"][app_id]
        set_disabled_ids(bot, disabled_ids)
        return True
    return False


def add_disabled_build_id(bot, build_id: str, note="") -> bool:
    disabled_ids = get_disabled_ids(bot)
    build_id = build_id.lower()
    if len(build_id) < 64:
        build_id += "0" * (64 - len(build_id))
    if build_id not in disabled_ids["build_id"].keys():
        disabled_ids["build_id"][build_id] = note
        set_disabled_ids(bot, disabled_ids)
        return True
    return False


def remove_disabled_build_id(bot, build_id: str) -> bool:
    disabled_ids = get_disabled_ids(bot)
    build_id = build_id.lower()
    if len(build_id) < 64:
        build_id += "0" * (64 - len(build_id))
    if build_id in disabled_ids["build_id"].keys():
        del disabled_ids["build_id"][build_id]
        set_disabled_ids(bot, disabled_ids)
        return True
    return False
