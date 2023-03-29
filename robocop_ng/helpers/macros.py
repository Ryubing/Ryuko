import json
import os
from typing import Optional

MACROS_FILE = "data/macros.json"


def get_macros() -> dict[str, str]:
    if os.path.isfile(MACROS_FILE):
        with open(MACROS_FILE, "r") as f:
            return json.load(f)
    return {}


def set_macros(contents: dict[str, str]):
    with open(MACROS_FILE, "w") as f:
        json.dump(contents, f)


def get_macro(key: str) -> Optional[str]:
    macros = get_macros()
    key = key.lower()
    if key in macros.keys():
        return macros[key]
    return None


def add_macro(key: str, message: str) -> bool:
    macros = get_macros()
    key = key.lower()
    if key not in macros.keys():
        macros[key] = message
        set_macros(macros)
        return True
    return False


def edit_macro(key: str, message: str) -> bool:
    macros = get_macros()
    key = key.lower()
    if key in macros.keys():
        macros[key] = message
        set_macros(macros)
        return True
    return False


def remove_macro(key: str) -> bool:
    macros = get_macros()
    key = key.lower()
    if key in macros.keys():
        del macros[key]
        set_macros(macros)
        return True
    return False
