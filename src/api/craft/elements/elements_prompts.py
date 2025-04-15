from src.api.craft.elements.elements_schemas import Element, ElementInput, ElementOutput

ex_1_input = ElementInput(
    element_a=Element(name="Wind", emoji="🌬️"),
    element_b=Element(name="Earth", emoji="🌍"),
)
ex_1_output = ElementOutput(
    reason="Wind blowing across earth naturally lifts fine particles, creating dust. It's a logical environmental effect, not just combined words. Creative.",
    result=Element(name="Dust", emoji="🌫️"),
)

ex_2_input = ElementInput(
    element_a=Element(name="Fire", emoji="🔥"),
    element_b=Element(name="Earth", emoji="🌍"),
)
ex_2_output = ElementOutput(
    reason="Intense heat (fire) melting earth/rock forms lava. Represents a direct, real-world transformation of elements. Conceptually strong.",
    result=Element(name="Lava", emoji="🌋"),
)

ELEMENTS_COMBINATION_SYSTEM_PROMPT: str = """
You are a great alchemist combining elements to create new ones and provide a reason for the combination.
""".strip()

ELEMENTS_COMBINATION_QUERY: str = """
**Task:** Generate a creative element combination.

**Combination Rules:**
1.  **Conceptual Link:** 
2.  **Creativity:** The result should be a distinct new concept, not just a mix of the input names.
3.  **Conciseness:** The new element name should be short (typically 1-2 words).
4.  **Emoji:** Select a pretty and recognizable emoji for the new element.
5.  **Reason:** Provide a short, creative reason for the combination.
"""

ELEMENTS_COMBINATION_EXAMPLES: str = f"""
Input Schema:
```json
{Element.model_json_schema()}
```

Output Schema:
```json
{ElementOutput.model_json_schema()}
```

**Example 1**
Input:
```json
{ex_1_input}
```
Output:
```json
{ex_1_output}
```

**Example 2**
Input:
```json
{ex_2_input}
```
Output:
```json
{ex_2_output}
```
""".strip()
