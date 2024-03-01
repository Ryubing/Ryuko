import re
from enum import IntEnum, auto
from typing import Optional, Union

from robocop_ng.helpers.disabled_ids import is_build_id_valid
from robocop_ng.helpers.size import Size


class CommonError(IntEnum):
    SHADER_CACHE_COLLISION = auto()
    DUMP_HASH = auto()
    SHADER_CACHE_CORRUPTION = auto()
    UPDATE_KEYS = auto()
    FILE_PERMISSIONS = auto()
    FILE_NOT_FOUND = auto()
    MISSING_SERVICES = auto()
    VULKAN_OUT_OF_MEMORY = auto()


class RyujinxVersion(IntEnum):
    MASTER = auto()
    OLD_MASTER = auto()
    LDN = auto()
    MAC = auto()
    PR = auto()
    CUSTOM = auto()


class LogAnalyser:
    _log_text: str
    _log_errors: list[list[str]]
    _hardware_info: dict[str, Optional[str]]
    _emu_info: dict[str, Optional[str]]
    _game_info: dict[str, Optional[str]]
    _settings: dict[str, Optional[str]]
    _notes: Union[set[str], list[str]]

    @staticmethod
    def is_homebrew(log_file: str) -> bool:
        return (
            re.search("Load.*Application: Loading as [Hh]omebrew", log_file) is not None
        )

    @staticmethod
    def get_main_ro_section(log_file: str) -> Optional[dict[str, str]]:
        ro_section_matches = re.findall(
            r"PrintRoSectionInfo: main:[\r\n]((?:\s+.*[\r\n])*)", log_file
        )
        if ro_section_matches and len(ro_section_matches) > 0:
            ro_section_match: str = ro_section_matches[-1]
            ro_section = {"module": "", "sdk_libraries": []}
            if ro_section_match is None or len(ro_section_match) == 0:
                return None
            for line in ro_section_match.splitlines():
                line = line.strip()
                if line.startswith("Module:"):
                    ro_section["module"] = line[8:]
                elif line.startswith("SDK Libraries:"):
                    ro_section["sdk_libraries"].append(line[19:])
                elif line.startswith("SDK "):
                    ro_section["sdk_libraries"].append(line[4:])
                else:
                    break
            return ro_section
        return None

    @staticmethod
    def get_app_info(
        log_file: str,
    ) -> Optional[tuple[str, str, str, list[str], dict[str, str]]]:
        game_name_match = re.findall(
            r"Loader [A-Za-z]*: Application Loaded:\s([^;\n\r]*)",
            log_file,
            re.MULTILINE,
        )
        if game_name_match:
            game_name = game_name_match[-1].rstrip()
            app_id_match = re.match(r".* \[([a-zA-Z0-9]*)\]", game_name)
            if app_id_match:
                app_id = app_id_match.group(1).strip().upper()
            else:
                app_id = ""
            bids_match_all = re.findall(
                r"Build ids found for title ([a-zA-Z0-9]*):[\n\r]*((?:\s+.*[\n\r]+)+)",
                log_file,
            )
            if bids_match_all and len(bids_match_all) > 0:
                bids_match: tuple[str] = bids_match_all[-1]
                app_id_from_bids = None
                build_ids = None
                if bids_match[0] is not None:
                    app_id_from_bids = bids_match[0].strip().upper()
                if bids_match[1] is not None:
                    build_ids = [
                        bid.strip().upper()
                        for bid in bids_match[1].splitlines()
                        if is_build_id_valid(bid.strip())
                    ]

                return (
                    game_name,
                    app_id,
                    app_id_from_bids,
                    build_ids,
                    LogAnalyser.get_main_ro_section(log_file),
                )
        return None

    @staticmethod
    def contains_errors(search_terms, errors):
        for term in search_terms:
            for error_lines in errors:
                line = "\n".join(error_lines)
                if term in line:
                    return True
        return False

    def __init__(self, log_text: Union[str, list[str]]):
        self.__init_members()

        if isinstance(log_text, str):
            self._log_text = log_text.replace("\r\n", "\n")
        elif isinstance(log_text, list):
            self._log_text = "\n".join(log_text)
        else:
            raise TypeError(log_text)

        # Large files show a header value when not downloaded completely
        # this regex makes sure that the log text to read starts from the first timestamp, ignoring headers
        log_file_header_regex = re.compile(r"\d{2}:\d{2}:\d{2}\.\d{3}.*", re.DOTALL)
        log_file_match = re.search(log_file_header_regex, self._log_text)
        if log_file_match and log_file_match.group(0) is not None:
            self._log_text = log_file_match.group(0)
        else:
            raise ValueError("No log entries found.")

        self.__get_errors()
        self.__get_settings_info()
        self.__get_hardware_info()
        self.__get_ryujinx_info()
        self.__get_app_name()
        self.__get_mods()
        self.__get_cheats()
        self.__get_notes()

    def __init_members(self):
        self._hardware_info = {
            "cpu": "Unknown",
            "gpu": "Unknown",
            "ram": "Unknown",
            "os": "Unknown",
        }
        self._emu_info = {
            "ryu_version": "Unknown",
            "ryu_firmware": "Unknown",
            "logs_enabled": None,
        }
        self._game_info = {
            "game_name": "Unknown",
            "errors": "No errors found in log",
            "mods": "No mods found",
            "cheats": "No cheats found",
        }
        self._settings = {
            "audio_backend": "Unknown",
            "backend_threading": "Unknown",
            "docked": "Unknown",
            "expand_ram": "Unknown",
            "fs_integrity": "Unknown",
            "graphics_backend": "Unknown",
            "ignore_missing_services": "Unknown",
            "memory_manager": "Unknown",
            "pptc": "Unknown",
            "shader_cache": "Unknown",
            "vsync": "Unknown",
            "resolution_scale": "Unknown",
            "anisotropic_filtering": "Unknown",
            "aspect_ratio": "Unknown",
            "texture_recompression": "Unknown",
        }
        self._notes = set()
        self._log_errors = []

    def __get_errors(self):
        errors = []
        curr_error_lines = []
        error_line = False
        for line in self._log_text.splitlines():
            if len(line.strip()) == 0:
                continue
            if "|E|" in line:
                curr_error_lines = [line]
                errors.append(curr_error_lines)
                error_line = True
            elif error_line and line[0] == " ":
                curr_error_lines.append(line)
        if len(curr_error_lines) > 0:
            errors.append(curr_error_lines)

        self._log_errors = errors

    def __get_hardware_info(self):
        for setting in self._hardware_info.keys():
            match setting:
                case "cpu":
                    cpu_match = re.search(
                        r"CPU:\s([^;\n\r]*)", self._log_text, re.MULTILINE
                    )
                    if cpu_match is not None and cpu_match.group(1) is not None:
                        self._hardware_info[setting] = cpu_match.group(1).rstrip()

                case "ram":
                    sizes = "|".join(Size.names())
                    ram_match = re.search(
                        rf"RAM: Total ([\d.]+) ({sizes}) ; Available ([\d.]+) ({sizes})",
                        self._log_text,
                        re.MULTILINE,
                    )
                    if ram_match is not None:
                        try:
                            dest_unit = Size.MiB

                            ram_available = float(ram_match.group(3))
                            ram_available = Size.from_name(ram_match.group(4)).convert(
                                ram_available, dest_unit
                            )

                            ram_total = float(ram_match.group(1))
                            ram_total = Size.from_name(ram_match.group(2)).convert(
                                ram_total, dest_unit
                            )

                            self._hardware_info[setting] = (
                                f"{ram_available:.0f}/{ram_total:.0f} {dest_unit.name}"
                            )
                        except ValueError:
                            # ram_match.group(1) or ram_match.group(3) couldn't be parsed as a float.
                            self._hardware_info[setting] = "Error"

                case "os":
                    os_match = re.search(
                        r"Operating System:\s([^;\n\r]*)",
                        self._log_text,
                        re.MULTILINE,
                    )
                    if os_match is not None and os_match.group(1) is not None:
                        self._hardware_info[setting] = os_match.group(1).rstrip()

                case "gpu":
                    gpu_match = re.search(
                        r"PrintGpuInformation:\s([^;\n\r]*)",
                        self._log_text,
                        re.MULTILINE,
                    )
                    if gpu_match is not None and gpu_match.group(1) is not None:
                        self._hardware_info[setting] = gpu_match.group(1).rstrip()

                case _:
                    raise NotImplementedError(setting)

    def __get_ryujinx_info(self):
        for setting in self._emu_info.keys():
            match setting:
                case "ryu_version":
                    for line in self._log_text.splitlines():
                        if "Ryujinx Version:" in line:
                            self._emu_info[setting] = line.split()[-1].strip()
                            break

                case "logs_enabled":
                    logs_match = re.search(
                        r"Logs Enabled:\s([^;\n\r]*)", self._log_text, re.MULTILINE
                    )
                    if logs_match is not None and logs_match.group(1) is not None:
                        self._emu_info[setting] = logs_match.group(1).rstrip()

                case "ryu_firmware":
                    for line in self._log_text.splitlines():
                        if "Firmware Version:" in line:
                            self._emu_info[setting] = line.split()[-1].strip()
                            break

                case _:
                    raise NotImplementedError(setting)

    def __get_setting_value(self, name, key):
        values = [
            line.split()[-1]
            for line in self._log_text.splitlines()
            if re.search(rf"LogValueChange: ({key})\s", line)
        ]
        if len(values) > 0:
            value = values[-1]
        else:
            return None

        match name:
            case "docked":
                return "Docked" if value == "True" else "Handheld"

            case "resolution_scale":
                resolution_map = {
                    "-1": "Custom",
                    "1": "Native (720p/1080p)",
                    "2": "2x (1440p/2160p)",
                    "3": "3x (2160p/3240p)",
                    "4": "4x (2880p/4320p)",
                }
                if value in resolution_map.keys():
                    return resolution_map[value]
                else:
                    return "Custom"

            case "anisotropic_filtering":
                anisotropic_map = {
                    "-1": "Auto",
                    "2": "2x",
                    "4": "4x",
                    "8": "8x",
                    "16": "16x",
                }
                if value in anisotropic_map.keys():
                    return anisotropic_map[value]
                else:
                    return "Auto"

            case "aspect_ratio":
                aspect_map = {
                    "Fixed4x3": "4:3",
                    "Fixed16x9": "16:9",
                    "Fixed16x10": "16:10",
                    "Fixed21x9": "21:9",
                    "Fixed32x9": "32:9",
                    "Stretched": "Stretch to Fit Window",
                }
                if value in aspect_map.keys():
                    return aspect_map[value]
                else:
                    return "Unknown"

            case "pptc" | "shader_cache" | "texture_recompression" | "vsync":
                return "Enabled" if value == "True" else "Disabled"

            case _:
                return value

    def __get_settings_info(self):
        settings_map = {
            "anisotropic_filtering": "MaxAnisotropy",
            "aspect_ratio": "AspectRatio",
            "audio_backend": "AudioBackend",
            "backend_threading": "BackendThreading",
            "docked": "EnableDockedMode",
            "expand_ram": "ExpandRam",
            "fs_integrity": "EnableFsIntegrityChecks",
            "graphics_backend": "GraphicsBackend",
            "ignore_missing_services": "IgnoreMissingServices",
            "memory_manager": "MemoryManagerMode",
            "pptc": "EnablePtc",
            "resolution_scale": "ResScale",
            "shader_cache": "EnableShaderCache",
            "texture_recompression": "EnableTextureRecompression",
            "vsync": "EnableVsync",
        }

        for key in self._settings.keys():
            if key in settings_map:
                self._settings[key] = self.__get_setting_value(key, settings_map[key])
            else:
                raise NotImplementedError(key)

    def __get_mods(self):
        mods_regex = re.compile(r"Found mod\s\'(.+?)\'\s(\[.+?\])")
        matches = re.findall(mods_regex, self._log_text)
        if matches:
            mods = [{"mod": match[0], "status": match[1]} for match in matches]
            mods_status = [
                f"ℹ️ {i['mod']} ({'ExeFS' if i['status'] == '[E]' else 'RomFS'})"
                for i in mods
            ]
            # Remove duplicated mods from output
            mods_status = list(dict.fromkeys(mods_status))

            self._game_info["mods"] = "\n".join(mods_status)

    def __get_cheats(self):
        cheat_regex = re.compile(r"Tampering program\s<(.+)>")
        matches = re.findall(cheat_regex, self._log_text)
        if matches:
            cheats = [f"ℹ️ {match}" for match in matches]

            self._game_info["cheats"] = "\n".join(cheats)

    def __get_app_name(self):
        app_match = re.findall(
            r"Loader [A-Za-z]*: Application Loaded:\s([^;\n\r]*)",
            self._log_text,
            re.MULTILINE,
        )
        if app_match:
            self._game_info["game_name"] = app_match[-1].rstrip()

    def __get_controller_notes(self):
        controllers_regex = re.compile(r"Hid Configure: ([^\r\n]+)")
        controllers = re.findall(controllers_regex, self._log_text)
        if controllers:
            input_status = [f"ℹ {match}" for match in controllers]
            # Hid Configure lines can appear multiple times, so converting to dict keys removes duplicate entries,
            # also maintains the list order
            input_status = list(dict.fromkeys(input_status))
            self._notes.add("\n".join(input_status))
        # If emulator crashes on startup without game load, there is no need to show controller notification at all
        elif self._game_info["game_name"] != "Unknown":
            self._notes.add("⚠️ No controller information found")

    def __get_os_notes(self):
        if (
            "Windows" in self._hardware_info["os"]
            and self._settings["graphics_backend"] != "Vulkan"
        ):
            if "Intel" in self._hardware_info["gpu"]:
                self._notes.add(
                    "**⚠️ Intel iGPU users should consider using Vulkan graphics backend**"
                )
            if "AMD" in self._hardware_info["gpu"]:
                self._notes.add(
                    "**⚠️ AMD GPU users should consider using Vulkan graphics backend**"
                )

    def __get_log_notes(self):
        default_logs = ["Info", "Warning", "Error", "Guest"]
        user_logs = []
        if self._emu_info["logs_enabled"] is not None:
            user_logs = (
                self._emu_info["logs_enabled"].rstrip().replace(" ", "").split(",")
            )

        if "Debug" in user_logs:
            self._notes.add(
                "⚠️ **Debug logs enabled will have a negative impact on performance**"
            )

        disabled_logs = set(default_logs).difference(set(user_logs))
        if disabled_logs:
            logs_status = [f"⚠️ {log} log is not enabled" for log in disabled_logs]
            log_string = "\n".join(logs_status)
        else:
            log_string = "✅ Default logs enabled"

        self._notes.add(log_string)

    def __get_settings_notes(self):
        if self._settings["audio_backend"] == "Dummy":
            self._notes.add(
                "⚠️ Dummy audio backend, consider changing to SDL2 or OpenAL"
            )

        if self._settings["pptc"] == "Disabled":
            self._notes.add("🔴 **PPTC cache should be enabled**")

        if self._settings["shader_cache"] == "Disabled":
            self._notes.add("🔴 **Shader cache should be enabled**")

        if self._settings["expand_ram"] == "True":
            self._notes.add(
                "⚠️ `Use alternative memory layout` should only be enabled for 4K mods"
            )

        if self._settings["memory_manager"] == "SoftwarePageTable":
            self._notes.add(
                "🔴 **`Software` setting in Memory Manager Mode will give slower performance than the default setting of `Host unchecked`**"
            )

        if self._settings["ignore_missing_services"] == "True":
            self._notes.add(
                "⚠️ `Ignore Missing Services` being enabled can cause instability"
            )

        if self._settings["vsync"] == "Disabled":
            self._notes.add(
                "⚠️ V-Sync disabled can cause instability like games running faster than intended or longer load times"
            )

        if self._settings["fs_integrity"] == "Disabled":
            self._notes.add(
                "⚠️ Disabling file integrity checks may cause corrupted dumps to not be detected"
            )

        if self._settings["backend_threading"] == "Off":
            self._notes.add(
                "🔴 **Graphics Backend Multithreading should be set to `Auto`**"
            )

    def __sort_notes(self):
        def severity(log_note_string):
            symbols = ["❌", "🔴", "⚠️", "ℹ", "✅"]
            return next(
                i for i, symbol in enumerate(symbols) if symbol in log_note_string
            )

        game_notes = [note for note in self._notes]
        # Warnings split on the string after the warning symbol for alphabetical ordering
        # Severity key then orders alphabetically sorted warnings to show most severe first
        return sorted(sorted(game_notes, key=lambda x: x.split()[1]), key=severity)

    def __get_notes(self):
        for common_error in self.get_common_errors():
            match common_error:
                case CommonError.SHADER_CACHE_COLLISION:
                    self._notes.add(
                        "⚠️ Cache collision detected. Investigate possible shader cache issues"
                    )
                case CommonError.SHADER_CACHE_CORRUPTION:
                    self._notes.add(
                        "⚠️ Cache corruption detected. Investigate possible shader cache issues"
                    )
                case CommonError.DUMP_HASH:
                    self._notes.add(
                        "⚠️ Dump error detected. Investigate possible bad game/firmware dump issues"
                    )
                case CommonError.UPDATE_KEYS:
                    self._notes.add(
                        "⚠️ Keys or firmware out of date, consider updating them"
                    )
                case CommonError.FILE_PERMISSIONS:
                    self._notes.add(
                        "⚠️ File permission error. Consider deleting save directory and allowing Ryujinx to make a new one"
                    )
                case CommonError.FILE_NOT_FOUND:
                    self._notes.add(
                        "⚠️ Save not found error. Consider starting game without a save file or using a new save file"
                    )
                case CommonError.MISSING_SERVICES:
                    if self._settings["ignore_missing_services"] == "False":
                        self._notes.add(
                            "⚠️ Consider enabling `Ignore Missing Services` in Ryujinx settings"
                        )
                case CommonError.VULKAN_OUT_OF_MEMORY:
                    if self._settings["texture_recompression"] == "Disabled":
                        self._notes.add(
                            "⚠️ Consider enabling `Texture Recompression` in Ryujinx settings"
                        )
                case _:
                    raise NotImplementedError(common_error)

        timestamp_regex = re.compile(r"\d{2}:\d{2}:\d{2}\.\d{3}")
        latest_timestamp = re.findall(timestamp_regex, self._log_text)[-1]
        if latest_timestamp:
            timestamp_message = f"ℹ️ Time elapsed: `{latest_timestamp}`"
            self._notes.add(timestamp_message)

        if self.is_default_user_profile():
            self._notes.add(
                "⚠️ Default user profile in use, consider creating a custom one."
            )

        self.__get_controller_notes()
        self.__get_os_notes()

        if (
            self._emu_info["ryu_firmware"] == "Unknown"
            and self._game_info["game_name"] != "Unknown"
        ):
            firmware_warning = f"**❌ Nintendo Switch firmware not found**"
            self._notes.add(firmware_warning)

        self.__get_settings_notes()
        if self.get_ryujinx_version() == RyujinxVersion.CUSTOM:
            self._notes.add("**⚠️ Custom builds are not officially supported**")

    def get_ryujinx_version(self):
        mainline_version = re.compile(r"^\d\.\d\.\d+$")
        old_mainline_version = re.compile(r"^\d\.\d\.(\d){4}$")
        pr_version = re.compile(r"^\d\.\d\.\d\+([a-f]|\d){7}$")
        ldn_version = re.compile(r"^\d\.\d\.\d-ldn\d+\.\d+(?:\.\d+|$)")
        mac_version = re.compile(r"^\d\.\d\.\d-macos\d+(?:\.\d+(?:\.\d+|$)|$)")

        if re.match(mainline_version, self._emu_info["ryu_version"]):
            return RyujinxVersion.MASTER
        elif re.match(old_mainline_version, self._emu_info["ryu_version"]):
            return RyujinxVersion.OLD_MASTER
        elif re.match(mac_version, self._emu_info["ryu_version"]):
            return RyujinxVersion.MAC
        elif re.match(ldn_version, self._emu_info["ryu_version"]):
            return RyujinxVersion.LDN
        elif re.match(pr_version, self._emu_info["ryu_version"]):
            return RyujinxVersion.PR
        else:
            return RyujinxVersion.CUSTOM

    def is_default_user_profile(self) -> bool:
        return (
            re.search(r"UserId: 00000000000000010000000000000000", self._log_text)
            is not None
        )

    def get_last_error(self) -> Optional[list[str]]:
        return self._log_errors[-1] if len(self._log_errors) > 0 else None

    def get_common_errors(self) -> list[CommonError]:
        errors = []

        if self.contains_errors(["Cache collision found"], self._log_errors):
            errors.append(CommonError.SHADER_CACHE_COLLISION)
        if self.contains_errors(
            [
                "ResultFsInvalidIvfcHash",
                "ResultFsNonRealDataVerificationFailed",
            ],
            self._log_errors,
        ):
            errors.append(CommonError.DUMP_HASH)
        if self.contains_errors(
            [
                "Ryujinx.Graphics.Gpu.Shader.ShaderCache.Initialize()",
                "System.IO.InvalidDataException: End of Central Directory record could not be found",
                "ICSharpCode.SharpZipLib.Zip.ZipException: Cannot find central directory",
            ],
            self._log_errors,
        ):
            errors.append(CommonError.SHADER_CACHE_CORRUPTION)
        if self.contains_errors(["MissingKeyException"], self._log_errors):
            errors.append(CommonError.UPDATE_KEYS)
        if self.contains_errors(["ResultFsPermissionDenied"], self._log_errors):
            errors.append(CommonError.FILE_PERMISSIONS)
        if self.contains_errors(["ResultFsTargetNotFound"], self._log_errors):
            errors.append(CommonError.FILE_NOT_FOUND)
        if self.contains_errors(["ServiceNotImplementedException"], self._log_errors):
            errors.append(CommonError.MISSING_SERVICES)
        if self.contains_errors(["ErrorOutOfDeviceMemory"], self._log_errors):
            errors.append(CommonError.VULKAN_OUT_OF_MEMORY)

        return errors

    def analyse_discord(
        self, is_channel_allowed: bool, pr_channel: int
    ) -> dict[str, dict[str, str]]:
        last_error = self.get_last_error()
        if last_error is not None:
            last_error = "\n".join(last_error[:2])
            self._game_info["errors"] = f"```\n{last_error}\n```"
        else:
            self._game_info["errors"] = "No errors found in log"

        # Limit mods and cheats to 5 entries
        mods = self._game_info["mods"].splitlines()
        cheats = self._game_info["cheats"].splitlines()
        if len(mods) > 5:
            limit_mods = mods[:5]
            limit_mods.append(f"✂️ {len(mods) - 5} other mods")
            self._game_info["mods"] = "\n".join(limit_mods)
        if len(cheats) > 5:
            limit_cheats = cheats[:5]
            limit_cheats.append(f"✂️ {len(cheats) - 5} other cheats")
            self._game_info["cheats"] = "\n".join(limit_cheats)

        if is_channel_allowed and self.get_ryujinx_version() == RyujinxVersion.PR:
            self._notes.add(
                f"**⚠️ PR build logs should be posted in <#{pr_channel}> if reporting bugs or tests**"
            )

        self._notes = self.__sort_notes()
        full_game_info = self._game_info
        full_game_info["notes"] = (
            "\n".join(self._notes) if len(self._notes) > 0 else "Nothing to note"
        )

        return {
            "hardware_info": self._hardware_info,
            "emu_info": self._emu_info,
            "game_info": full_game_info,
            "settings": self._settings,
        }

    def analyse(self) -> dict[str, Union[dict[str, str], list[str], list[list[str]]]]:
        self._notes = list(self.__sort_notes())

        last_error = self.get_last_error()
        if last_error is not None:
            last_error = "\n".join(last_error[:2])
            self._game_info["errors"] = f"```\n{last_error}\n```"
        else:
            self._game_info["errors"] = "No errors found in log"

        return {
            "hardware_info": self._hardware_info,
            "emu_info": self._emu_info,
            "game_info": self._game_info,
            "notes": self._notes,
            "errors": self._log_errors,
            "settings": self._settings,
            "app_info": self.get_app_info(self._log_text),
        }


if __name__ == "__main__":
    import argparse
    import json
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument("log_file", type=str)

    args = parser.parse_args()

    if not os.path.isfile(args.log_file):
        print(f"Couldn't find log file: {args.log_file}")
        exit(1)

    with open(args.log_file, "r") as file:
        text = file.read()

    analyser = LogAnalyser(text)
    result = analyser.analyse()

    print(json.dumps(result, indent=2))
