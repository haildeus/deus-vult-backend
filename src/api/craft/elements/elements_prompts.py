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

ELEMENTS_COMBINATION_SYSTEM_PROMPT: str = f"""
You are an element combiner. Combine the two input elements (name + emoji) to create **one** new resulting element (name + emoji).

**Guidelines:**
- The resulting element must be a combination of the two input elements.
- It must contain name and emoji.
- Prioritize **unique** and **creative** combinations.

**Example 1:**
{ex_1_input.model_dump_json()}
{ex_1_output.model_dump_json()}

**Example 2:**
{ex_2_input.model_dump_json()}
{ex_2_output.model_dump_json()}

**Example 3:**
{ex_3_input.model_dump_json()}
{ex_3_output.model_dump_json()}

**Example 4:**
{ex_4_input.model_dump_json()}
{ex_4_output.model_dump_json()}
""".strip()
