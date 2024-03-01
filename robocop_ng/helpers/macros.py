import json
import os
from typing import Optional, Union

from robocop_ng.helpers.data_loader import read_json


def get_macros_path(bot):
    return os.path.join(bot.state_dir, "data/macros.json")


def get_macros_dict(bot) -> dict[str, dict[str, Union[list[str], str]]]:
    macros = read_json(bot, get_macros_path(bot))
    if len(macros) > 0:
        # Migration code
        if "aliases" not in macros.keys():
            new_macros = {"macros": macros, "aliases": {}}
            unique_macros = set(new_macros["macros"].values())
            for macro_text in unique_macros:
                first_macro_key = ""
                duplicate_num = 0
                for key, macro in new_macros["macros"].copy().items():
                    if macro == macro_text and duplicate_num == 0:
                        first_macro_key = key
                        duplicate_num += 1
                        continue
                    elif macro == macro_text:
                        if first_macro_key not in new_macros["aliases"].keys():
                            new_macros["aliases"][first_macro_key] = []
                        new_macros["aliases"][first_macro_key].append(key)
                        del new_macros["macros"][key]
                        duplicate_num += 1

            set_macros(bot, new_macros)
            return new_macros

        return macros
    return {"macros": {}, "aliases": {}}


def is_macro_key_available(
    bot, key: str, macros: dict[str, dict[str, Union[list[str], str]]] = None
) -> bool:
    if macros is None:
        macros = get_macros_dict(bot)
    if key in macros["macros"].keys():
        return False
    for aliases in macros["aliases"].values():
        if key in aliases:
            return False
    return True


def set_macros(bot, contents: dict[str, dict[str, Union[list[str], str]]]):
    with open(get_macros_path(bot), "w") as f:
        json.dump(contents, f)


def get_macro(bot, key: str) -> Optional[str]:
    macros = get_macros_dict(bot)
    key = key.lower()
    if key in macros["macros"].keys():
        return macros["macros"][key]
    for main_key, aliases in macros["aliases"].items():
        if key in aliases:
            return macros["macros"][main_key]
    return None


def add_macro(bot, key: str, message: str) -> bool:
    macros = get_macros_dict(bot)
    key = key.lower()
    if is_macro_key_available(bot, key, macros):
        macros["macros"][key] = message
        set_macros(bot, macros)
        return True
    return False


def add_aliases(bot, key: str, aliases: list[str]) -> bool:
    macros = get_macros_dict(bot)
    key = key.lower()
    success = False
    if key in macros["macros"].keys():
        for alias in aliases:
            alias = alias.lower()
            if is_macro_key_available(bot, alias, macros):
                if key not in macros["aliases"].keys():
                    macros["aliases"][key] = []
                macros["aliases"][key].append(alias)
                success = True
        if success:
            set_macros(bot, macros)
    return success


def edit_macro(bot, key: str, message: str) -> bool:
    macros = get_macros_dict(bot)
    key = key.lower()
    if key in macros["macros"].keys():
        macros["macros"][key] = message
        set_macros(bot, macros)
        return True
    return False


def remove_aliases(bot, key: str, aliases: list[str]) -> bool:
    macros = get_macros_dict(bot)
    key = key.lower()
    success = False
    if key not in macros["aliases"].keys():
        return False
    for alias in aliases:
        alias = alias.lower()
        if alias in macros["aliases"][key]:
            macros["aliases"][key].remove(alias)
            if len(macros["aliases"][key]) == 0:
                del macros["aliases"][key]
            success = True
    if success:
        set_macros(bot, macros)
    return success


def remove_macro(bot, key: str) -> bool:
    macros = get_macros_dict(bot)
    key = key.lower()
    if key in macros["macros"].keys():
        del macros["macros"][key]
        set_macros(bot, macros)
        return True
    return False


def clear_aliases(bot, key: str) -> bool:
    macros = get_macros_dict(bot)
    key = key.lower()
    if key in macros["macros"].keys() and key in macros["aliases"].keys():
        del macros["aliases"][key]
        set_macros(bot, macros)
        return True
    return False
