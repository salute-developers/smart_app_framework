import json


def make_serializable(obj):
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, set):
        return {make_serializable(subobj) for subobj in obj}
    elif isinstance(obj, list):
        return [make_serializable(subobj) for subobj in obj]
    elif isinstance(obj, tuple):
        return tuple(make_serializable(subobj) for subobj in obj)
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        return str(obj)
