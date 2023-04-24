from typing import List, Tuple, Any

from core.logging.logger_utils import log
from smart_kit.utils.object_location import ObjectLocation


def ssml_string_parser(obj: Any, location: ObjectLocation) -> List[Tuple[str, ObjectLocation]]:
    ssml_strings = []
    if isinstance(obj, dict):
        # For pattern (dict contain ["command": "ANSWER_TO_USER"; nodes.pronounceTextType = "application/ssml"])
        # get nodes.pronounceText
        if obj.get("command") == "ANSWER_TO_USER" \
                and obj.get("nodes", {}).get("pronounceTextType") == "application/ssml" \
                and not obj.get("no_ssml_check"):
            if "pronounceText" not in obj["nodes"]:
                log(f"Missing nodes.pronounceText in {ObjectLocation(location.object_location + ['nodes'])}",
                    level="WARNING")
            else:
                ssml_strings.append((obj["nodes"]["pronounceText"],
                                     ObjectLocation(location.object_location + ["nodes", "pronounceText"])))
        for field_key, field_val in obj.items():
            ssml_strings.extend(ssml_string_parser(field_val, ObjectLocation(location.object_location + [field_key])))
    elif isinstance(obj, (list, set, tuple)):
        for i, val in enumerate(obj):
            ssml_strings.extend(ssml_string_parser(val, ObjectLocation(location.object_location + [f"[{i}]"])))
    return ssml_strings
