import re
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from dataclasses import field
from typing import Any, List, Dict, Optional

import core.logging.logger_constants as log_const
from core.basic_models.actions.basic_actions import Action
from core.basic_models.actions.command import Command
from core.logging.logger_utils import log
from core.text_preprocessing.base import BaseTextPreprocessingResult
from scenarios.user.user_model import User


_VersionType = Optional[str]


@dataclass
class ServiceVersions:
    dp_code_version: _VersionType = field(metadata={"name": "Dialog Policy code"})
    dp_static_version: _VersionType = field(metadata={"name": "Dialog Policy static"})

    @classmethod
    def init_from_user(cls, user: User) -> "ServiceVersions":
        return cls(
            dp_code_version=user.settings.version.code_version,
            dp_static_version=user.settings.version.static_version,
        )


class ShowVersionsAction(Action):
    COMMAND = "ANSWER_TO_USER"
    REQUEST_TYPE = "kafka"
    REQUEST_DATA = {
        "topic_key": "vps",
        "kafka_key": "main",
    }

    async def run(
        self,
        user: User,
        text_preprocessing_result: BaseTextPreprocessingResult,
        params: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Command, None]:
        params = {**(params or {}), **user.parametrizer.collect(text_preprocessing_result)}

        versions = ServiceVersions.init_from_user(user)
        log(
            f"{self.__class__.__name__} {versions}",
            params={log_const.KEY_NAME: "show_versions_action"},
        )
        command_params = {
            "items": self._get_items(versions),
            "pronounceText": self._get_pronounce_text(versions),
            "pronounceTextType": "application/ssml",
            "character": {"id": params["get_character_data"]()["id"]},
            "voice": params["get_tts_voice_id"](),
        }

        yield Command(
            name=self.COMMAND,
            params=command_params,
            action_id=self.id,
            request_type=self.REQUEST_TYPE,
            request_data=self.REQUEST_DATA,
        )

    @staticmethod
    def _get_items(versions: ServiceVersions) -> List[Dict[str, Dict[str, str]]]:
        parts = [
            f"**Dialog Policy**\nкод: {versions.dp_code_version}\nстатики: {versions.dp_static_version}\n\n",
        ]
        text = "".join(parts)
        text = text.strip()
        return [{"bubble": {"text": text, "markdown": True}}]

    def _get_pronounce_text(self, versions: ServiceVersions) -> str:
        dp_code_ssml = self._version_to_ssml(versions.dp_code_version or "")
        dp_static_ssml = self._version_to_ssml(versions.dp_static_version or "")

        parts = [
            "<speak>",
            f'Dialog Policy: <break time="200ms"/> версия кода <break time="400ms"/> {dp_code_ssml};',
            f'Dialog Policy: <break time="200ms"/> версия статиков <break time="400ms"/> {dp_static_ssml};',
            "</speak>",
        ]
        return "\n".join(parts)

    @staticmethod
    def _version_to_ssml(version: str) -> str:
        expr = re.compile(r"^D-(\d+).(\d+).(\d+)-(\d+)$")
        match = expr.match(version)
        if not match:
            return "bad format"
        ssml_groups = [f'<say-as interpret-as="digits">{gr}</say-as>' for gr in match.groups()]
        return (
            '<say-as interpret-as="characters">D</say-as>-' +
            f"{ssml_groups[0]}.{ssml_groups[1]}.{ssml_groups[2]}-{ssml_groups[3]}"
        )
