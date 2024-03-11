"""
# Модуль с переопределёнными сущностями NLPF для работы StateMachine.

* В `app_config.py` необходимо добавить следующее:

```python
from nlpf_statemachine.override import DialogueManagerSM, SmartAppModelSM
...
DIALOGUE_MANAGER = DialogueManagerSM
MODEL = SmartAppModelSM
...
```
"""

from .dialogue_manager import SMDialogueManager
from .model_config import SMSmartAppResources
from .repository import SMRepository
from .smartapp_model import (
    SMDefaultMessageHandler,
    SMHandlerCloseApp,
    SMHandlerServerAction,
    SMHandlerTimeout,
    SMSmartAppModel,
)
from .user import SMUser

__all__ = [
    "SMUser",
    "SMDialogueManager",
    "SMSmartAppModel",
    "SMSmartAppResources",
    "SMDefaultMessageHandler",
    "SMHandlerCloseApp",
    "SMHandlerServerAction",
    "SMHandlerTimeout",
    "SMRepository",
]

# Legacy!
StateMachineAppsUser = SMUser
DialogueManagerSM = SMDialogueManager
SmartAppModelSM = SMSmartAppModel
