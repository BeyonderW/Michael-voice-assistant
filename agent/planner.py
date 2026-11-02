"""agent/planner.py - Generates structured JSON execution plans via Groq."""

import json
from typing import Any, Dict, List
from agent.tools import TOOL_REGISTRY

MAX_STEPS = 5

PLANNER_SYSTEM_PROMPT = f"""You are the Task Planning Core for Michael, a Windows AI assistant.
Your job is to translate user requests into a strictly valid JSON execution plan.

Available Tools:
{json.dumps({k: {"description": v['description'], "required_args": v['required_args']} for k, v in TOOL_REGISTRY.items()}, indent=2)}

Rules:
1. Output MUST be a valid JSON object matching the schema below. No Markdown code fences, no extra text.
2. Max steps allowed: {MAX_STEPS}. Keep the plan minimal, linear, and sequential.
3. Every step tool MUST match an exact tool name from Available Tools.
4. Arguments MUST strictly match expected tool parameters.
5. If the request cannot be met with the available tools, return an empty steps list with an explanation.

JSON Schema:
{{
  "goal": "string (the overarching objective)",
  "steps": [
    {{
      "step_id": 1,
      "tool": "string (tool name)",
      "args": {{ "param_name": "value" }},
      "expected_outcome": "string describing what successful completion looks like"
    }}
  ],
  "reasoning": "brief explanation of the plan"
}}
"""


class TaskPlanner:
    def __init__(self, groq_client, model_name: str = "openai/gpt-oss-120b"):
        self.client = groq_client
        self.model_name = model_name

    def plan(self, user_goal: str) -> Dict[str, Any]:
        """Call Groq to produce a structured JSON action plan."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Create an execution plan for: {user_goal}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )

        content = response.choices[0].message.content
        print(f"\n[DEBUG] RAW LLM PLAN: {content}\n") 
        plan_data = json.loads(content)

        # Enforce hard constraints
        steps: List[Dict[str, Any]] = plan_data.get("steps", [])
        if len(steps) > MAX_STEPS:
            plan_data["steps"] = steps[:MAX_STEPS]

        return plan_data