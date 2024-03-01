import json
import os
from typing import Union

from robocop_ng.helpers.data_loader import read_json


def get_disabled_ids_path(bot) -> str:
    return os.path.join(bot.state_dir, "data/disabled_ids.json")


def is_app_id_valid(app_id: str) -> bool:
    return len(app_id) == 16 and app_id.isalnum()


def is_build_id_valid(build_id: str) -> bool:
    return 32 <= len(build_id) <= 64 and build_id.isalnum()


def is_ro_section_valid(ro_section: dict[str, str]) -> bool:
    return "module" in ro_section.keys() and "sdk_libraries" in ro_section.keys()


def get_disabled_ids(bot) -> dict[str, dict[str, Union[str, dict[str, str]]]]:
    disabled_ids = read_json(bot, get_disabled_ids_path(bot))
    if len(disabled_ids) > 0:
        # Migration code
        if "app_id" in disabled_ids.keys():
            old_disabled_ids = disabled_ids.copy()
            disabled_ids = {}
            for key in old_disabled_ids["app_id"].values():
                disabled_ids[key.lower()] = {
                    "app_id": "",
                    "build_id": "",
                    "ro_section": {},
                }
            for id_type in ["app_id", "build_id"]:
                for value, key in old_disabled_ids[id_type].items():
                    disabled_ids[key.lower()][id_type] = value
            for key, value in old_disabled_ids["ro_section"].items():
                disabled_ids[key.lower()]["ro_section"] = value
            set_disabled_ids(bot, disabled_ids)

    return disabled_ids


def set_disabled_ids(bot, contents: dict[str, dict[str, Union[str, dict[str, str]]]]):
    with open(get_disabled_ids_path(bot), "w") as f:
        json.dump(contents, f)


def add_disable_id_if_necessary(
    disable_id: str, disabled_ids: dict[str, dict[str, Union[str, dict[str, str]]]]
):
    if disable_id not in disabled_ids.keys():
        disabled_ids[disable_id] = {"app_id": "", "build_id": "", "ro_section": {}}


def is_app_id_disabled(bot, app_id: str) -> bool:
    disabled_app_ids = [
        entry["app_id"]
        for entry in get_disabled_ids(bot).values()
        if len(entry["app_id"]) > 0
    ]
    app_id = app_id.lower()
    return app_id in disabled_app_ids


def is_build_id_disabled(bot, build_id: str) -> bool:
    disabled_build_ids = [
        entry["build_id"]
        for entry in get_disabled_ids(bot).values()
        if len(entry["build_id"]) > 0
    ]
    build_id = build_id.lower()
    if len(build_id) < 64:
        build_id += "0" * (64 - len(build_id))
    return build_id in disabled_build_ids


def is_ro_section_disabled(bot, ro_section: dict[str, Union[str, list[str]]]) -> bool:
    disabled_ro_sections = [
        entry["ro_section"]
        for entry in get_disabled_ids(bot).values()
        if len(entry["ro_section"]) > 0
    ]
    matches = []
    for disabled_ro_section in disabled_ro_sections:
        for key, content in disabled_ro_section.items():
            if key == "module":
                matches.append(ro_section[key].lower() == content.lower())
            else:
                matches.append(ro_section[key] == content)
            if all(matches) and len(matches) > 0:
                return True
            else:
                matches = []
        return False


def remove_disable_id(bot, disable_id: str) -> bool:
    disabled_ids = get_disabled_ids(bot)
    if disable_id in disabled_ids.keys():
        del disabled_ids[disable_id]
        set_disabled_ids(bot, disabled_ids)
        return True
    return False


def add_disabled_app_id(bot, disable_id: str, app_id: str) -> bool:
    disabled_ids = get_disabled_ids(bot)
    disable_id = disable_id.lower()
    app_id = app_id.lower()
    if not is_app_id_disabled(bot, app_id):
        add_disable_id_if_necessary(disable_id, disabled_ids)
        disabled_ids[disable_id]["app_id"] = app_id
        set_disabled_ids(bot, disabled_ids)
        return True
    return False


def add_disabled_build_id(bot, disable_id: str, build_id: str) -> bool:
    disabled_ids = get_disabled_ids(bot)
    disable_id = disable_id.lower()
    build_id = build_id.lower()
    if len(build_id) < 64:
        build_id += "0" * (64 - len(build_id))
    if not is_build_id_disabled(bot, build_id):
        add_disable_id_if_necessary(disable_id, disabled_ids)
        disabled_ids[disable_id]["build_id"] = build_id
        set_disabled_ids(bot, disabled_ids)
        return True
    return False


def remove_disabled_app_id(bot, disable_id: str) -> bool:
    disabled_ids = get_disabled_ids(bot)
    disable_id = disable_id.lower()
    if (
        disable_id in disabled_ids.keys()
        and len(disabled_ids[disable_id]["app_id"]) > 0
    ):
        disabled_ids[disable_id]["app_id"] = ""
        set_disabled_ids(bot, disabled_ids)
        return True
    return False


def remove_disabled_build_id(bot, disable_id: str) -> bool:
    disabled_ids = get_disabled_ids(bot)
    disable_id = disable_id.lower()
    if (
        disable_id in disabled_ids.keys()
        and len(disabled_ids[disable_id]["build_id"]) > 0
    ):
        disabled_ids[disable_id]["build_id"] = ""
        set_disabled_ids(bot, disabled_ids)
        return True
    return False


def add_disabled_ro_section(
    bot, disable_id: str, ro_section: dict[str, Union[str, list[str]]]
) -> bool:
    disabled_ids = get_disabled_ids(bot)
    disable_id = disable_id.lower()
    add_disable_id_if_necessary(disable_id, disabled_ids)
    if len(ro_section) > len(disabled_ids[disable_id]["ro_section"]):
        for key, content in ro_section.items():
            if key == "module":
                disabled_ids[disable_id]["ro_section"][key] = content.lower()
            else:
                disabled_ids[disable_id]["ro_section"][key] = content
        set_disabled_ids(bot, disabled_ids)
        return True
    return False


def remove_disabled_ro_section(bot, disable_id: str) -> bool:
    disabled_ids = get_disabled_ids(bot)
    disable_id = disable_id.lower()
    if (
        disable_id in disabled_ids.keys()
        and len(disabled_ids[disable_id]["ro_section"]) > 0
    ):
        disabled_ids[disable_id]["ro_section"] = {}
        set_disabled_ids(bot, disabled_ids)
        return True
    return False
