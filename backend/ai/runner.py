import json
import sys
from pydantic import ValidationError
import yaml
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import time

from backend.models import RylandState
from backend.ai.state_updates import (
    apply_description,
    apply_resources,
    apply_course_length,
    apply_weeks,
    apply_assignment_list,
    apply_assignment_details,
    apply_quizzes
)

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.ai.client import get_client

AI_DIR = Path(__file__).parent
DEFAULT_SYSTEM_PROMPT = "You are an expert AI assistant. Return only valid JSON, no markdown, no explanation."

DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
FALLBACK_MODELS = [
    "meta-llama/llama-4-scout-17b-16e-instruct",  # 30K TPM, 500K TPD
    "llama-3.3-70b-versatile",  # 12K TPM, 100K TPD
    "qwen/qwen3-32b",  # 6K TPM, 500K TPD
    "llama-3.1-8b-instant",  # 6K TPM, 500K TPD
]


# --- Model ---


def call_model(prompt: str, system_prompt: str, model: str = DEFAULT_MODEL) -> str:
    models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]
    last_error = None

    for m in models_to_try:
        try:
            client = get_client()
            response = client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=4000,
            )
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("No response from AI")
            return content

        except Exception as e:
            last_error = e
            if "rate_limit" in str(e) or "429" in str(e):
                print(f"Rate limit hit for {m}, trying next model...")
            else:
                print(f"Error from {m}, {e}, trying next model...")
            continue

    raise RuntimeError(f"All models failed. Last error: {last_error}")


def parse_json_response(content: str) -> dict:
    if not content or content.strip() == "":
        raise ValueError("Cannot parse empty content as JSON")

    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    try:
        return json.loads(content, strict=False)
    except json.JSONDecodeError:
        import re

        content = re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", content)
        return json.loads(content, strict=False)


def load_pipeline_context(stages_dir: Path) -> tuple[str, str, str]:
    """Returns (identity_md, workspace_context, system_prompt)"""
    identity_md = (stages_dir.parent.parent / "IDENTITY.md").read_text()

    workspace_raw = (stages_dir.parent / "CONTEXT.md").read_text()
    _, workspace_frontmatter, workspace_context = workspace_raw.split("---", 2)
    workspace_meta = yaml.safe_load(workspace_frontmatter)
    system_prompt = workspace_meta.get("system_prompt", DEFAULT_SYSTEM_PROMPT)

    return identity_md, workspace_context, system_prompt


def load_stage_context(stage_path: Path) -> tuple[dict, str]:
    """Returns (meta, context)"""
    context_raw = (stage_path / "CONTEXT.md").read_text()
    _, frontmatter, context = context_raw.split("---", 2)
    meta = yaml.safe_load(frontmatter)
    return meta, context


def load_references(stage_path: Path) -> str:
    references = ""
    ref_path = stage_path / "references"
    if ref_path.exists():
        for f in ref_path.glob("*.md"):
            references += f"\n\n# {f.stem}\n{f.read_text()}"
    return references


# --- Prompt building ---


def build_prompt(
    identity_md: str,
    workspace_context: str,
    context: str,
    references: str,
    state_context: dict,
) -> str:
    return f"""
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

## Current Course State
{json.dumps(state_context, indent=2)}
"""


# --- Stage execution ---


def get_loop_items(loop_over: str, state: RylandState):
    if loop_over == "weeks":
        return state.course.weeks

    if loop_over == "assignments":
        return [
            assignment
            for week in state.course.weeks
            for assignment in week.assignments
        ]

    raise ValueError(f"Unknown loop target: {loop_over}")


def run_loop_stage(
    stage_name: str,
    loop_over: str,
    full_prompt: str,
    state: RylandState,
    system_prompt: str,
    model: str,
) -> None:

    items = get_loop_items(loop_over, state)

    total = len(items)
    completed = 0

    def process_item(item, index):
        nonlocal completed
        content = call_model(
            full_prompt + f"\n\n## Current Item\n{json.dumps(item.model_dump(mode='json'), indent=2)}",
            system_prompt,
            model,
        )
        try:
            result = parse_json_response(content)

        except (ValueError, json.JSONDecodeError) as e:
            print(f"Failed to parse item {index}: {e}")
            return None

        completed += 1
        print(f"loop {completed}/{total} done: {getattr(item, 'title', index)}")
        return result

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {}
        for i, item in enumerate(items):
            futures[executor.submit(process_item, item, i)] = i
            time.sleep(1)

        for future, i in futures.items():
            result = future.result()

            if result is None:
                continue
            try:
                apply_stage_result(
                    stage_name,
                    result,
                    state,
                    items[i],
                )

            except ValidationError as e:
                print(f"Skipping invalid result for item {i}: {e}")


def build_state_context(state: RylandState) -> dict:
    return state.model_dump(mode="json")


_STAGE_HANDLERS = {
    "01_course_description": apply_description,
    "02_course_resources": apply_resources,
    "03_course_length": apply_course_length,
    "04_weekly_goal": apply_weeks,
    "05_assignments": apply_assignment_list,
    "06_assignment_description": apply_assignment_details,
    "07_generate_quizzes": apply_quizzes,
}

_LOOP_ITEM_STAGES = {"05_assignments", "06_assignment_description"}


def apply_stage_result(stage_name: str, result: dict, state: RylandState, current_item=None):
    handler = _STAGE_HANDLERS.get(stage_name)
    if not handler:
        return
    if stage_name in _LOOP_ITEM_STAGES:
        handler(result, current_item)
    else:
        handler(result, state)


def run_stage(
    stage_name: str,
    state: RylandState,
    stages_dir: Path = AI_DIR / "curriculum" / "stages",
) -> None:
    print(f"Running stage {stage_name}")

    stage_path = stages_dir / stage_name

    identity_md, workspace_context, system_prompt = load_pipeline_context(stages_dir)
    meta, context = load_stage_context(stage_path)
    references = load_references(stage_path)
    state_context = build_state_context(state)

    for key, value in state.request.model_dump().items():
        context = context.replace(f"{{{key}}}", str(value))

    full_prompt = build_prompt(
        identity_md, workspace_context, context, references, state_context
    )

    loop_over = meta.get("loop_over")
    model = meta.get("model", DEFAULT_MODEL)

    if loop_over:
        result = run_loop_stage(
            stage_name,
            loop_over,
            full_prompt,
            state,
            system_prompt,
            model,
        )
    else:
        content = call_model(full_prompt, system_prompt, model)
        result = parse_json_response(content)

        apply_stage_result(stage_name, result, state)
        print(state.course.model_dump(mode="json"))
