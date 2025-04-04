"""
This file contains the utils code for the dspy optimization.
"""

import json
import random
from typing import Any

import dspy  # type: ignore
from dspy.evaluate import Evaluate  # type: ignore
from dspy.teleprompt import BootstrapFewShotWithRandomSearch  # type: ignore
from jsonschema import ValidationError
from pydantic import BaseModel, Field

from src.api.craft.elements.elements_schemas import Element
from src.shared.base_llm import VertexConfig, VertexLLM

"""
PREPARING DATA
"""
# --- LM Config ---
vertex_config = VertexConfig()
vertex_llm_object = VertexLLM(vertex_config)
gemini_model = dspy.LM("vertex_ai/gemini-2.0-flash-lite-001")
dspy.configure(lm=gemini_model)  # type: ignore


# --- Input/Output Schemas ---
class Input(BaseModel):
    element_a: Element = Field(..., description="The first element to combine")
    element_b: Element = Field(..., description="The second element to combine")


class Output(BaseModel):
    result: Element = Field(
        ...,
        description="The element resulting from the combination of the two input elements",
    )


"""
EVALUATION PREP
"""


# --- Data Loading ---
def load_data(filename: str = "utils/combo_data.json"):
    with open(filename) as f:
        combo_data = json.load(f)
    return combo_data


def get_data(
    combo_data: list[dict[Any, Any]], position: int = 0
) -> tuple[Input, Output] | None:
    """Safely extracts Input and Output objects from loaded data at a given position."""
    if not combo_data or position >= len(combo_data):  # # type: ignore
        print(
            f"Warning: Position {position} is out of bounds for data length {len(combo_data)}."
        )
        return None
    try:
        combo_entry = combo_data[position]  # type: ignore
        element_a = Element(**combo_entry["input_a"])  # type: ignore
        element_b = Element(**combo_entry["input_b"])  # type: ignore
        result = Element(**combo_entry["result"])  # type: ignore

        input_object = Input(element_a=element_a, element_b=element_b)
        output_object = Output(result=result)

        return input_object, output_object
    except (KeyError, TypeError, ValidationError) as e:
        print(
            f"Warning: Failed to parse data at position {position}. Error: {e}. Entry: {combo_entry}"  # type: ignore
        )
        return None


# --- Training Data ---
print("---Loading data---")
combo_data = load_data()
random.shuffle(combo_data)

total_data_len = len(combo_data)
training_data_len = int(total_data_len * 0.7)
test_data_len = total_data_len - training_data_len
print(
    f"Total examples: {total_data_len}, Training: {training_data_len}, Testing: {test_data_len}"
)
training_objects = [get_data(combo_data, i) for i in range(training_data_len)]
test_objects = [
    get_data(combo_data, i) for i in range(training_data_len, total_data_len)
]
print(
    f"Valid training objects: {len(training_objects)}, Valid test objects: {len(test_objects)}"
)
training_array: list[dict[str, Input | Output]] = [
    {"input": input_obj, "output": output_obj}
    for input_obj, output_obj in training_objects
]
test_array: list[dict[str, Input | Output]] = [
    {"input": input_obj, "output": output_obj} for input_obj, output_obj in test_objects
]


# Loading examples
print("---Loading examples---")
trainset: list[dspy.Example] = [
    dspy.Example(**data).with_inputs("input")  # type: ignore
    for data in training_array
]
# Use test_array for testset, ensure it's not empty if needed
if test_array:
    testset: list[dspy.Example] = [
        dspy.Example(**data).with_inputs("input")  # type: ignore
        for data in test_array
    ]
else:
    print(
        "Warning: Test set is empty after filtering. Using training set for validation."
    )
    testset = trainset  # Fallback if testset is empty, though not ideal

print(
    f"---Loaded {len(trainset)} training examples and {len(testset)} testing examples---"
)


def combined_metric(gold: dspy.Example, pred: dspy.Example, trace: Any = None) -> bool:
    """
    Checks for:
    1.  Format Adherence: If the prediction ('pred.output') was successfully parsed into the Output schema.
    2.  Non-Empty Result: If the resulting element has both name and emoji.
    3.  Input Non-Repetition: If the result is different from both inputs.
    """
    # 1. Format Adherence & Non-Empty check
    try:
        # Check if DSPy successfully parsed the output into our Pydantic model
        predicted_output = pred.output  # type: ignore
        if not isinstance(predicted_output, Output):
            print(
                f"Validation Fail: pred.output is not type Output. Type: {type(predicted_output)}"
            )
            return False

        result_element = predicted_output.result
        if not isinstance(result_element, Element):  # type: ignore
            print(
                f"Validation Fail: result is not type Element. Type: {type(result_element)}"
            )
            return False

        # Check if essential fields are present and non-empty
        if not result_element.name or not result_element.emoji:
            print(
                f"Validation Fail: Result name or emoji is empty. Result: {result_element}"
            )
            return False

    except (AttributeError, TypeError, Exception) as e:
        print(f"Validation Fail: Error accessing predicted output structure: {e}")
        return False

    # 2. Input Non-Repetition check
    try:
        input_a = gold.input.element_a  # type: ignore
        input_b = gold.input.element_b  # type: ignore
        output_result = pred.output.result  # type: ignore

        # Check if output matches input_a
        if (
            output_result.name == input_a.name  # type: ignore
            and output_result.emoji == input_a.emoji  # type: ignore
        ):
            print(
                f"Validation Fail: Output '{output_result}' matches Input A '{input_a}'"
            )
            return False

        # Check if output matches input_b
        if (
            output_result.name == input_b.name  # type: ignore
            and output_result.emoji == input_b.emoji  # type: ignore
        ):
            print(
                f"Validation Fail: Output '{output_result}' matches Input B '{input_b}'"
            )
            return False

    except AttributeError as e:
        print(f"Validation Fail: Error accessing gold input structure: {e}")
        return False

    # If all checks pass
    return True


"""
PROGRAM PREP
"""


class GenerateCombinationSignature(dspy.Signature):
    """
    Given two elements (each with a name and emoji), creatively determine what new element they combine to form.
    Provide the resulting element name and emoji.
    Follow the provided JSON schema for the 'output' field strictly. Only output the JSON.
    """

    input: Input = dspy.InputField(description="The two elements to combine")  # type: ignore
    output: Output = dspy.OutputField(  # type: ignore
        description="The resulting element in JSON format matching the Output schema",
        # Pydantic schema for DSPy to enforce structure
        # ** Important: DSPy uses this to generate formatting instructions for the LM **
    )


"""
OPTIMIZATION
"""

boostrapping_config = {
    "max_bootstrapped_demos": 4,  # Max demos per prompt
    "max_labeled_demos": 4,  # Max labeled examples to consider for demos
    "num_candidate_programs": 10,  # Number of prompt variations to try
    "num_threads": 4,  # Parallel evaluations
}

print("---Initializing fewshot optimizer with COMBINED metric---")
# Use the new, more robust metric
fewshot_optimizer = BootstrapFewShotWithRandomSearch(
    metric=combined_metric,  # Use the new metric here
    **boostrapping_config,
)

"""
RUN
"""
if not testset:
    print("ERROR: Test set is empty. Cannot run optimizer validation.")
    effective_valset = trainset
else:
    effective_valset = testset

combine_elements_program = dspy.ChainOfThought(GenerateCombinationSignature)

print("---Running fewshot optimizer---")
optimized_program = fewshot_optimizer.compile(  # type: ignore
    student=combine_elements_program,
    trainset=trainset,
    valset=effective_valset,
)
print("---Fewshot optimizer finished---")
"""
EVALUATE (Optional but recommended)
"""
print("---Evaluating the optimized program on the test set---")
evaluate = Evaluate(
    devset=testset,
    metric=combined_metric,
    num_threads=4,
    display_progress=True,
    display_table=True,
)
score = evaluate(optimized_program)  # type: ignore
print(f"---Final evaluation score on test set using combined_metric: {score:.2f}% ---")

print("---Inspecting optimized program before saving---")
if hasattr(optimized_program, "demos") and optimized_program.demos:
    print(f"Found {len(optimized_program.demos)} demos directly on the program object.")
elif (
    hasattr(optimized_program, "predictor")
    and hasattr(optimized_program.predictor, "demos")
    and optimized_program.predictor.demos
):
    print(
        f"Found {len(optimized_program.predictor.demos)} demos on the program's predictor."
    )
    # Also print the demos themselves to see if they look right
    # for demo in optimized_program.predictor.demos:
    #    print(demo)
else:
    print(
        "WARNING: No demos found on the optimized program object or its predictor before saving."
    )

"""
SAVE
"""
print("---Saving optimized program---")
save_path = "optimized_combo_program_v2.json"
optimized_program.save(save_path)
print(f"Optimized program saved to {save_path}")
