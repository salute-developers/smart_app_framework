"""
# Моки различных типов сообщений в апп.
"""
from __future__ import annotations

from random import choice, randint

from core.logging.logger_utils import behaviour_log
from nlpf_statemachine.const import AssistantAthena, AssistantJoy, AssistantSber
from nlpf_statemachine.example.app.sc.models.message import CustomCurrentApp, CustomMeta
from nlpf_statemachine.models import (
    Annotations,
    AppInfo,
    AssistantId,
    AssistantMessage,
    AssistantMeta,
    AssistantState,
    BaseMessage,
    Character,
    CloseApp,
    CurrentApp,
    Device,
    LocalTimeout,
    Message,
    MessageToSkill,
    MessageToSkillPayload,
    RunApp,
    SelectedItem,
    ServerAction,
    ServerActionMessage,
    ServerActionPayload,
    Strategies,
    Surface,
    UUID,
)
from nlpf_statemachine.utils.base_utils import get_field_class
from tests.nlpf_statemachine_tests.utils.base import random_string, random_guid


class MessageMocks:
    """
    # Моки различных типов сообщений в апп.
    """

    @staticmethod
    def app_info() -> AppInfo:
        """## Мок объекта AppInfo."""
        return AppInfo(
            projectId=random_guid(),
            frontendType="WEB_APP",
        )

    @staticmethod
    def character(character_id: AssistantId | None = AssistantId.athena) -> Character:
        """## Мок объекта Character."""
        characters: dict[AssistantId, Character] = {
            AssistantId.joy: AssistantJoy,
            AssistantId.athena: AssistantAthena,
            AssistantId.sber: AssistantSber,
        }
        if character_id in characters:
            return characters[character_id]
        return choice(characters.values())

    @staticmethod
    def meta(
            cls: type[AssistantMeta] = AssistantMeta,
            state: dict | AssistantState | None = None,
    ) -> AssistantMeta:
        """## Мок объекта AssistantMeta."""
        current_app_cls = CustomCurrentApp if cls.__name__ == 'CustomMeta' else CurrentApp
        meta = cls(
            current_app=current_app_cls(
                state=state,
            ),
        )
        behaviour_log(f"META: {meta}")
        return meta

    @staticmethod
    def uuid(sub: str | None = None, user_id: str | None = None, user_channel: str | None = None) -> UUID:
        """## Мок объекта UUID."""
        return UUID(
            sub=sub if sub else random_string(length=100),
            userId=user_id if user_id else random_string(length=30),
            userChannel=user_channel if user_channel else choice(["SBOL"]),
        )

    @staticmethod
    def message(
            original_text: str | None = None,
            normalized_text: str | None = None,
            asr_normalized_message: str | None = None,
            entities: dict | None = None,
            tokenized_elements_list: list[str] | None = None,
    ) -> Message:
        """## Мок объекта Message."""
        return Message(
            original_text=original_text if original_text else random_string(),
            normalized_text=normalized_text if normalized_text else random_string(),
            entities=entities if entities else {},
            asr_normalized_message=asr_normalized_message if asr_normalized_message else random_string(),
            tokenized_elements_list=tokenized_elements_list if tokenized_elements_list else [],
        )

    @staticmethod
    def device() -> Device:
        """## Мок объекта Device."""
        return Device(
            platformType=random_string(),
            platformVersion=random_string(),
            surface=choice(list(Surface)),
            surfaceVersion=random_string(),
            deviceId=random_string(),
            features=None,
            capabilities=None,
            additionalInfo={},
        )

    @staticmethod
    def strategies() -> Strategies:
        """## Мок объекта Strategies."""
        return Strategies(
            happy_birthday=False,
            is_alice=False,
        )

    @staticmethod
    def server_action(
            action_id: str | None = None,
            parameters: dict | None = None,
    ) -> ServerAction:
        """## Мок объекта ServerAction."""
        return ServerAction(
            action_id=action_id if action_id else random_string(),
            parameters=parameters if parameters else None,
        )

    # ==== Message Mocks ====
    def message_to_skill(
            self,
            cls: type[MessageToSkill] = MessageToSkill,
            original_text: str | None = None,
            normalized_text: str | None = None,
            asr_normalized_message: str | None = None,
            entities: dict | None = None,
            tokenized_elements_list: list | None = None,
            intent: str | None = None,
            original_intent: str | None = None,
            selected_item: dict | SelectedItem | None = None,
            project_name: str | None = None,
            uuid: dict | UUID | None = None,
            character_id: str | AssistantId | None = AssistantId.athena,
            state: dict | AssistantState | None = None,
            annotations: dict | Annotations | None = None,
            app_info: dict | AppInfo | None = None,
            device: dict | Device | None = None,
            new_session: bool = False,
            strategies: dict | Strategies | None = None,
    ) -> MessageToSkill:
        """
        ## Мок объекта MessageToSkill.
        """
        payload_cls: type[MessageToSkillPayload] = get_field_class(base_obj=cls, field="payload")
        meta_cls: type[AssistantMeta] = get_field_class(base_obj=payload_cls, field="meta")

        return cls(
            messageId=randint(0, 100000000),
            sessionId=random_guid(),
            uuid=uuid if uuid else self.uuid(),
            payload=payload_cls(
                message=self.message(
                    original_text=original_text,
                    normalized_text=normalized_text,
                    asr_normalized_message=asr_normalized_message,
                    entities=entities,
                    tokenized_elements_list=tokenized_elements_list,
                ),
                app_info=app_info if app_info else self.app_info(),
                intent=intent,
                original_intent=original_intent,
                projectName=project_name if project_name else random_string(length=30),
                character=self.character(character_id=character_id),
                meta=self.meta(cls=meta_cls, state=state),
                selected_item=selected_item if selected_item else None,
                annotations=annotations if annotations else None,
                device=device if device else self.device(),
                new_session=new_session,
                strategies=strategies if strategies else self.strategies(),
                client_profile={},
            ),
        )

    def server_action_message(
            self,
            cls: type[ServerActionMessage] = ServerActionMessage,
            action_id: str | None = None,
            parameters: dict | None = None,
            intent: str | None = None,
            original_intent: str | None = None,
            project_name: str | None = None,
            uuid: dict | UUID | None = None,
            character_id: str | AssistantId | None = AssistantId.athena,
            state: dict | AssistantState | None = None,
            app_info: dict | AppInfo | None = None,
            device: dict | Device | None = None,
            new_session: bool = False,
            strategies: dict | Strategies | None = None,
    ) -> ServerActionMessage:
        """## Мок объекта ServerActionMessage."""
        return cls(
            messageId=randint(0, 100000000),
            sessionId=random_guid(),
            uuid=uuid if uuid else self.uuid(),
            payload=ServerActionPayload(
                server_action=self.server_action(action_id=action_id, parameters=parameters),
                app_info=app_info if app_info else self.app_info(),
                intent=intent,
                original_intent=original_intent,
                projectName=project_name if project_name else random_string(length=30),
                character=self.character(character_id=character_id),
                meta=self.meta(state=state),
                device=device if device else self.device(),
                new_session=new_session,
                strategies=strategies if strategies else self.strategies(),
                client_profile={},
            ),
        )

    def local_timeout(
            self,
            cls: type[LocalTimeout] = LocalTimeout,
            message: BaseMessage | None = None,
    ) -> LocalTimeout:
        """## Мок объекта LocalTimeout."""
        if not message:
            message = self.message_to_skill()
        return cls(
            messageId=message.messageId,
            sessionId=message.sessionId,
            uuid=message.uuid,
            payload=message.payload.model_dump(),
        )

    def run_app(
            self,
            cls: type[RunApp] = RunApp,
            message: BaseMessage | None = None,
    ) -> RunApp:
        """## Мок объекта RunApp."""
        if not message:
            message = self.server_action_message()
        return cls(
            messageId=message.messageId,
            sessionId=message.sessionId,
            uuid=message.uuid,
            payload=message.payload.model_dump(),
        )

    def close_app(
            self,
            cls: type[CloseApp] = CloseApp,
            message: AssistantMessage | None = None,
    ) -> CloseApp:
        """## Мок объекта CloseApp."""
        if not message:
            message = self.message_to_skill()
        return cls(
            messageId=message.messageId,
            sessionId=message.sessionId,
            uuid=message.uuid,
            payload=message.payload.model_dump(),
        )
