from src.api.craft.elements.elements_schemas import Element, ElementInput, ElementOutput

ex_1_input = ElementInput(
    element_a=Element(name="Electricity", emoji="⚡"),
    element_b=Element(name="Air", emoji="💨"),
)
ex_1_output = ElementOutput(
    result=Element(name="Storm", emoji="🌪️"),
)

ex_2_input = ElementInput(
    element_a=Element(name="Dragon", emoji="🐉"),
    element_b=Element(name="Pond", emoji="🌊"),
)
ex_2_output = ElementOutput(
    result=Element(name="Loch Ness Monster", emoji="🐊"),
)

ex_3_input = ElementInput(
    element_a=Element(name="Hawaii", emoji="🌺"),
    element_b=Element(name="Matcha", emoji="🍵"),
)
ex_3_output = ElementOutput(
    result=Element(name="Green Tea", emoji="🍵"),
)

ex_4_input = ElementInput(
    element_a=Element(name="Fish", emoji="🐟"),
    element_b=Element(name="Glacier", emoji="❄️"),
)
ex_4_output = ElementOutput(
    result=Element(name="Penguin", emoji="🐧"),
)

ELEMENTS_COMBINATION_SYSTEM_PROMPT: str = """
Combine two input elements to create a new element with name and emoji, return JSON.
""".strip()

ELEMENTS_COMBINATION_QUERY: str = """
Combine two elements in creative way to create a new element with name and emoji.
Return valid JSON.
"""

ELEMENTS_COMBINATION_EXAMPLES: str = """
**Input:**
```json
{input}
```

Schema:
```json
{Element.model_json_schema()}
```

**Example 1:**
```json
{ex_1_input.model_dump_json()}
{ex_1_output.model_dump_json()}
```

**Example 2:**
```json
{ex_2_input.model_dump_json()}
{ex_2_output.model_dump_json()}
```
""".strip()
