"""
# Моки различных типов сообщений в апп.
"""
from random import choice, randint
from typing import Dict, List, Optional, Type, Union

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
    def character(character_id: Optional[AssistantId] = AssistantId.athena) -> Character:
        """## Мок объекта Character."""
        characters: Dict[AssistantId, Character] = {
            AssistantId.joy: AssistantJoy,
            AssistantId.athena: AssistantAthena,
            AssistantId.sber: AssistantSber,
        }
        if character_id in characters:
            return characters[character_id]
        return choice(characters.values())

    @staticmethod
    def meta(
            cls: Type[AssistantMeta] = AssistantMeta,
            state: Optional[Union[Dict, AssistantState]] = None,
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
    def uuid(sub: Optional[str] = None, user_id: Optional[str] = None, user_channel: Optional[str] = None) -> UUID:
        """## Мок объекта UUID."""
        return UUID(
            sub=sub if sub else random_string(length=100),
            userId=user_id if user_id else random_string(length=30),
            userChannel=user_channel if user_channel else choice(["SBOL"]),
        )

    @staticmethod
    def message(
            original_text: Optional[str] = None,
            normalized_text: Optional[str] = None,
            asr_normalized_message: Optional[str] = None,
            entities: Optional[Dict] = None,
            tokenized_elements_list: Optional[List[str]] = None,
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
            action_id: Optional[str] = None,
            parameters: Optional[Dict] = None,
    ) -> ServerAction:
        """## Мок объекта ServerAction."""
        return ServerAction(
            action_id=action_id if action_id else random_string(),
            parameters=parameters if parameters else None,
        )

    # ==== Message Mocks ====
    def message_to_skill(
            self,
            cls: Type[MessageToSkill] = MessageToSkill,
            original_text: Optional[str] = None,
            normalized_text: Optional[str] = None,
            asr_normalized_message: Optional[str] = None,
            entities: Optional[Dict] = None,
            tokenized_elements_list: Optional[List] = None,
            intent: Optional[str] = None,
            original_intent: Optional[str] = None,
            selected_item: Optional[Union[Dict, SelectedItem]] = None,
            project_name: Optional[str] = None,
            uuid: Optional[Union[Dict, UUID]] = None,
            character_id: Optional[Union[str, AssistantId]] = AssistantId.athena,
            state: Optional[Union[Dict, AssistantState]] = None,
            annotations: Optional[Union[Dict, Annotations]] = None,
            app_info: Optional[Union[Dict, AppInfo]] = None,
            device: Optional[Union[Dict, Device]] = None,
            new_session: bool = False,
            strategies: Optional[Union[Dict, Strategies]] = None,
    ) -> MessageToSkill:
        """
        ## Мок объекта MessageToSkill.
        """
        payload_cls: Type[MessageToSkillPayload] = get_field_class(base_obj=cls, field="payload")
        meta_cls: Type[AssistantMeta] = get_field_class(base_obj=payload_cls, field="meta")

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
            cls: Type[ServerActionMessage] = ServerActionMessage,
            action_id: Optional[str] = None,
            parameters: Optional[Dict] = None,
            intent: Optional[str] = None,
            original_intent: Optional[str] = None,
            project_name: Optional[str] = None,
            uuid: Optional[Union[Dict, UUID]] = None,
            character_id: Optional[Union[str, AssistantId]] = AssistantId.athena,
            state: Optional[Union[Dict, AssistantState]] = None,
            app_info: Optional[Union[Dict, AppInfo]] = None,
            device: Optional[Union[Dict, Device]] = None,
            new_session: bool = False,
            strategies: Optional[Union[Dict, Strategies]] = None,
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
            cls: Type[LocalTimeout] = LocalTimeout,
            message: Optional[BaseMessage] = None,
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
            cls: Type[RunApp] = RunApp,
            message: Optional[BaseMessage] = None,
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
            cls: Type[CloseApp] = CloseApp,
            message: Optional[AssistantMessage] = None,
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
