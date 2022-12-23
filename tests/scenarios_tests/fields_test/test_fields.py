# coding: utf-8

from unittest import TestCase
from unittest.mock import Mock

from scenarios.scenario_models.field.fields import Fields
from smart_kit.utils.picklable_mock import PicklableMock


class TestFields(TestCase):

    def test_1(self):
        lifetime = 777
        descr1, descr2 = Mock(id="descr1"), Mock(id="descr2")
        items = {"descr1": PicklableMock(), "descr2": 2}
        descriptions = {"descr1": descr1, "descr2": descr2}

        def factory(descr, raw_data, user, lifetime):
            return Mock(value=raw_data, lifetime=lifetime, description=descr)
        user = PicklableMock()
        fields = Fields(items, descriptions, user, factory, lifetime=lifetime)
        values = fields.values
        self.assertEqual(items, values)
        for field in fields:
            f = fields[field]
            self.assertEqual(lifetime, f.lifetime)
