"""
# Поведение шторки ассистента.

Параметр актуален при работе с ассистентом на наших устройствах.

Возможные значения:

* `auto_expand` --— шторка будет автоматически разворачиваться,
  если полученный текст не помещается в свёрнутой шторке;
* `force_expand` —-- шторка развернётся независимо от того, помещается полученный текст в свёрнутой шторке или нет;
* `preserve_panel_state` --— сохраняет текущее состояние шторки независимо от длины текста.
По умолчанию auto_expand.
"""
from .smart_enum import SmartEnum


class TextBubbleExpandPolicy(SmartEnum):
    """
    # Список поведений шторки ассистента.
    """

    AUTO_EXPAND = "auto_expand"
    FORCE_EXPAND = "force_expand"
    PRESERVE_PANEL_STATE = "preserve_panel_state"
