import core.names.field as core_field

CALLBACK_ID_HEADER = "app_callback_id"
LINK_BEHAVIOR_FLAG = "link_previous_behavior"
KAFKA = "kafka"
KAFKA_REPLY_TOPIC = "kafka_replyTopic"

ORIGINAL_INTENT = "original_intent"
NEW_SESSION = "new_session"

SAVED_BEHAVIOR_PARAMS_FIELDS = {core_field.INTENT, core_field.INTENT_META,
                                ORIGINAL_INTENT, core_field.APP_INFO, core_field.PROJECT_NAME, NEW_SESSION,
                                core_field.APPLICATION_ID, core_field.APP_VERSION_ID}
