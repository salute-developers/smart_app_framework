import asyncio
from unittest import TestCase

from core.unified_template.unified_template import UnifiedTemplate, UNIFIED_TEMPLATE_TYPE_NAME


class TestUnifiedTemplate(TestCase):
    async def test_ordinar_jinja_backward_compatibility(self):
        template = UnifiedTemplate("abc {{input}}")
        self.assertEqual("abc def", await template.render({"input": "def"}))

    async def test_type_cast_int(self):
        template = UnifiedTemplate({
            "type": UNIFIED_TEMPLATE_TYPE_NAME,
            "loader": "int",
            "template": "{{ input ** 2 }}"
        })
        self.assertEqual(49, await template.render({"input": 7}))

    async def test_type_cast_json(self):
        template = UnifiedTemplate({
            "type": UNIFIED_TEMPLATE_TYPE_NAME,
            "loader": "json",
            "template": "{{ input }}"
        })
        self.assertEqual([1, 2, 3], await template.render({"input": [1, 2, 3]}))

    async def test_support_templates(self):
        template = UnifiedTemplate({
            "type": UNIFIED_TEMPLATE_TYPE_NAME,
            "support_templates": {
                "name": "{{ personInfo.name|capitalize }}",
                "surname": "{{ personInfo.surname|capitalize }}"
            },
            "template": "{{ name }} {{ surname }}",
        })
        self.assertEqual("Vasya Pupkin", await template.render({"personInfo": {"name": "vasya", "surname": "pupkin"}}))

    async def test_args_format_input(self):
        template = UnifiedTemplate("timestamp: {{ts}}")
        self.assertEqual("timestamp: 123.45", await template.render(ts=123.45))

    async def test_bool_cast_false(self):
        template = UnifiedTemplate({
            "type": UNIFIED_TEMPLATE_TYPE_NAME,
            "loader": "bool",
            "template": "False"
        })
        self.assertFalse(await template.render({}))

    async def test_bool_cast_false_lowercase(self):
        template = UnifiedTemplate({
            "type": UNIFIED_TEMPLATE_TYPE_NAME,
            "loader": "bool",
            "template": "false"
        })
        self.assertFalse(await template.render({}))

    async def test_bool_cast_true(self):
        template = UnifiedTemplate({
            "type": UNIFIED_TEMPLATE_TYPE_NAME,
            "loader": "bool",
            "template": "True"
        })
        self.assertTrue(await template.render({}))

    async def test_bool_cast_true_lowercase(self):
        template = UnifiedTemplate({
            "type": UNIFIED_TEMPLATE_TYPE_NAME,
            "loader": "bool",
            "template": "true"
        })
        self.assertTrue(await template.render({}))

    async def test_async(self):
        template = UnifiedTemplate("{{ some_foo(1, 42) }}")

        async def some_foo(a, b):
            await asyncio.sleep(0.1)
            return a + b

        params = {
            "some_foo": some_foo
        }
        rendered = await template.render(**params)
        self.assertEqual(rendered, 43)
