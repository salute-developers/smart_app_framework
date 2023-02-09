import orjson


def ordered_json(data):
    return orjson.loads(data)


def reverse_json_dict(data):
    data = orjson.loads(data)
    result = dict()
    for key, values in data.items():
        for value in values:
            result[value] = key
    return result
