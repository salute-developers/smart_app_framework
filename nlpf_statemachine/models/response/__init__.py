"""Модели ответа."""
from .assistant_response import (
    ASRHints,
    ASRHintsEOUPhraseMatch,
    AssistantCommand,
    AssistantResponse,
    AssistantResponsePayload,
    BaseCommand,
    Bubble,
    CanvasAppItem,
    Emotion,
    SmartAppDataCommand,
    TextBubble,
)
from .base_response import Response
from .custom_responses import DoNothing, ErrorResponse, IntegrationResponse, NothingFound
from .run_app_response import PolicyRunApp, PolicyRunAppPayload, PolicyRunAppServerAction

# Улучшает читаемость (?)
AnswerToUser = AssistantResponse

__all__ = [
    ASRHints,
    ASRHintsEOUPhraseMatch,
    AnswerToUser,
    AssistantCommand,
    AssistantResponse,
    AssistantResponsePayload,
    BaseCommand,
    Bubble,
    CanvasAppItem,
    DoNothing,
    Emotion,
    ErrorResponse,
    IntegrationResponse,
    NothingFound,
    PolicyRunApp,
    PolicyRunAppPayload,
    PolicyRunAppServerAction,
    Response,
    SmartAppDataCommand,
    TextBubble,
]

# Legacy! Не использовать!
ResponsePayload = AssistantResponsePayload
SmartAppCommand = SmartAppDataCommand
