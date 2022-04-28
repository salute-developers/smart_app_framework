import json


def make_serializable(obj):
    if isinstance(obj, dict):
        filtered = dict()
        for k, v in obj.items():
            filtered[k] = make_serializable(v)
        return filtered
    elif isinstance(obj, set):
        filtered = set()
        for subobj in obj:
            filtered.add(make_serializable(subobj))
        return filtered
    elif isinstance(obj, list):
        filtered = list()
        for subobj in obj:
            filtered.append(make_serializable(subobj))
        return filtered
    elif isinstance(obj, tuple):
        filtered = list()
        for subobj in obj:
            filtered.append(make_serializable(subobj))
        return tuple(filtered)
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        return str(obj)
