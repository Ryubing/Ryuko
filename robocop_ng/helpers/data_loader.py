import json
import os

from robocop_ng.helpers.notifications import report_critical_error


def read_json(bot, filepath: str) -> dict:
    if os.path.isfile(filepath) and os.path.getsize(filepath) > 0:
        with open(filepath, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                content = f.read()
                report_critical_error(
                    bot,
                    e,
                    additional_info={
                        "file": {"length": len(content), "content": content}
                    },
                )
    return {}
