"""
# Пример использования ContextManager.
"""
from core.logging.logger_utils import behaviour_log
from nlpf_statemachine.example.app.sc.example_1_static_storage import scenario as static_storage_scenario
from nlpf_statemachine.example.app.sc.example_2_integration import scenario as integration_scenario
from nlpf_statemachine.example.app.sc.example_3_server_action_and_commands import scenario as server_action_scenario
from nlpf_statemachine.example.app.sc.example_4_form_and_intersection_clf import scenario as form_filling_scenario
from nlpf_statemachine.example.app.sc.example_5_isolated_scenario import run_app_condition
from nlpf_statemachine.example.app.sc.example_5_isolated_scenario import scenario as run_app_scenario
from nlpf_statemachine.example.app.sc.example_6_pre_process import pre_process_condition
from nlpf_statemachine.example.app.sc.example_6_pre_process import scenario as pre_process_scenario
from nlpf_statemachine.example.app.sc.fallback import fallback
from nlpf_statemachine.example.app.sc.pre_post_process import post_process, pre_process
from nlpf_statemachine.kit import ContextManager, Form

behaviour_log("==== ИНИЦИАЛИЗАЦИЯ ContextManager ====")

# 1. Создаём инстанс ContextManager для нашего аппа.
context_manager = ContextManager()

# 2. Создаём глобальную форму для нашего аппа.
#    Не обязательный шаг, но удобен для отдельных кейсов.
form = Form()
context_manager.add_form(form=form)

# 3. Добавление изолированных сценариев в ContextManager.
context_manager.add_isolated_scenario(
    condition=run_app_condition,
    scenario=run_app_scenario,
)
context_manager.add_isolated_scenario(
    condition=pre_process_condition,
    scenario=pre_process_scenario,
)

# 4. Добавление сценариев в ContextManager.
context_manager.add_scenario(scenario=static_storage_scenario)
context_manager.add_scenario(scenario=integration_scenario)
context_manager.add_scenario(scenario=server_action_scenario)
context_manager.add_scenario(scenario=form_filling_scenario)

# 4. Добавление Fallback Action.
context_manager.add_fallback_action(action=fallback)

# 5. Добавление Pre и Post процессов
context_manager.add_pre_process(process=pre_process)
context_manager.add_post_process(process=post_process)
behaviour_log("==== ИНИЦИАЛИЗАЦИЯ ContextManager ОКОНЧЕНА ====")
