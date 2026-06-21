import json
import sys
from pathlib import Path


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.ai.client import client

STAGES_DIR = Path(__file__).parent / "stages"


def run_stage(stage_name: str, user_inputs: dict = {}) -> dict:
    stage_path = STAGES_DIR / stage_name
    output_path = stage_path / "output"
    output_path.mkdir(exist_ok=True)

    # Read stage contract (Layer 2)
    context = (stage_path / "CONTEXT.md").read_text()

    # Read global identity (Layer 0)
    identity_md = (STAGES_DIR.parent / "IDENTITY.md").read_text()

    # Read workspace routing (Layer 1)
    workspace_context = (STAGES_DIR.parent / "CONTEXT.md").read_text()

    # Read reference material (Layer 3)
    references = ""
    ref_path = stage_path / "references"
    if ref_path.exists():
        for f in ref_path.glob("*.md"):
            references += f"\n\n# {f.stem}\n{f.read_text()}"

    # Read previous stage outputs (Layer 4)
    previous_outputs = {}
    for prev_stage in sorted(STAGES_DIR.iterdir()):
        if prev_stage.name >= stage_name:
            break
        prev_output = prev_stage / "output" / "result.json"
        if prev_output.exists():
            previous_outputs[prev_stage.name] = json.loads(prev_output.read_text())

    # Substitute user inputs into context
    for key, value in user_inputs.items():
        context = context.replace(f"{{{key}}}", str(value))

    # Build full prompt
    full_prompt = f"""
{identity_md}

---

{workspace_context}

---

## Stage Contract
{context}

---

## Reference Material
{references}

---

## Previous Stage Outputs
{json.dumps(previous_outputs, indent=2)}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert curriculum designer. Return only valid JSON, no markdown, no explanation."},
            {"role": "user", "content": full_prompt}
        ]
    )

    content = response.choices[0].message.content
    if content is None:
        raise ValueError("No response from AI")

    result = json.loads(content)

    # Save output to disk (Layer 4 for next stage)
    (output_path / "result.json").write_text(json.dumps(result, indent=2))

    return result


if __name__ == "__main__":
    """
    result_01 = run_stage("01_course_description", {"course_name": "Introduction to Natural Language Processing"})
    print("Stage 01:", result_01)

    result_02 = run_stage("02_course_length")
    print("Stage 02:", result_02)
    """

    result_03 = run_stage("03_weekly_goal")
    print("Stage 03:", result_03)
