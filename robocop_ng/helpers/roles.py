import json
import os.path

PERSISTENT_ROLES_FILE = "data/persistent_roles.json"


def get_persistent_roles() -> dict[str, list[str]]:
    if os.path.isfile(PERSISTENT_ROLES_FILE):
        with open(PERSISTENT_ROLES_FILE, "r") as f:
            return json.load(f)
    return {}


def set_persistent_roles(contents: dict[str, list[str]]):
    with open(PERSISTENT_ROLES_FILE, "w") as f:
        json.dump(contents, f)


def add_user_roles(uid: int, roles: list[int]):
    uid = str(uid)
    roles = [str(x) for x in roles]

    persistent_roles = get_persistent_roles()
    persistent_roles[uid] = roles
    set_persistent_roles(persistent_roles)


def get_user_roles(uid: int) -> list[str]:
    uid = str(uid)
    with open(PERSISTENT_ROLES_FILE, "r") as f:
        roles = json.load(f)
        if uid in roles:
            return roles[uid]
        return []
