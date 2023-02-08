import ujson


def ordered_json(data):
    return ujson.loads(data)


def reverse_json_dict(data):
    data = ujson.loads(data)
    result = dict()
    for key, values in data.items():
        for value in values:
            result[value] = key
    return result
