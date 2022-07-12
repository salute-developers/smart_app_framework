import pickle


def pickle_deepcopy(obj):
    if isinstance(obj, dict):
        return {pickle_deepcopy(k): pickle_deepcopy(v) for k, v in obj.items()}
    elif isinstance(obj, set):
        return {pickle_deepcopy(subobj) for subobj in obj}
    elif isinstance(obj, list):
        return [pickle_deepcopy(subobj) for subobj in obj]
    elif isinstance(obj, tuple):
        return tuple(pickle_deepcopy(subobj) for subobj in obj)
    if hasattr(obj, "__call__"):
        return obj
    return pickle.loads(pickle.dumps(obj, -1))
