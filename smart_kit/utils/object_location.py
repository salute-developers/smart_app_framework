from typing import List


class ObjectLocation:
    def __init__(self, object_location: List[str]):
        self.object_location = object_location

    def __str__(self):
        return '.'.join(self.object_location)
