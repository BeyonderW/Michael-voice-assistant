"""agent/engine.py - Constrained Execution Engine with verification and safety guards."""

import concurrent.futures
import time
from typing import Any, Callable, Dict, List, Optional
from agent.tools import TOOL_REGISTRY


class TaskExecutionEngine:
    def __init__(self, step_timeout_seconds: int = 8, confirm_callback: Optional[Callable[[str], bool]] = None):
        self.step_timeout_seconds = step_timeout_seconds
        # Confirmation callback receives a warning string and returns True to proceed, False to abort
        self.confirm_callback = confirm_callback or self._default_console_confirmation

    @staticmethod
    def _default_console_confirmation(action_desc: str) -> bool:
        """Fallback confirmation hook via terminal input."""
        prompt = f"[CONFIRMATION REQUIRED] Michael is about to execute: {action_desc}. Proceed? (y/n): "
        return input(prompt).strip().lower() in ("y", "yes")

    def execute_plan(self, plan: Dict[str, Any], status_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Sequentially execute plan steps, verify outcomes, and stop immediately on failure."""
        goal = plan.get("goal", "Multi-step task")
        steps = plan.get("steps", [])
        execution_log: List[Dict[str, Any]] = []

        if not steps:
            return {
                "success": False,
                "summary": "Plan contained no executable steps.",
                "logs": execution_log
            }

        for idx, step in enumerate(steps, start=1):
            step_id = step.get("step_id", idx)
            tool_name = step.get("tool")
            args = step.get("args", {})
            expected = step.get("expected_outcome", "")

            step_record = {
                "step_id": step_id,
                "tool": tool_name,
                "args": args,
                "status": "PENDING",
                "output": None,
                "verification": None,
                "error": None
            }

            if status_callback:
                status_callback(f"Step {step_id}/{len(steps)}: Running {tool_name}...")

            # 1. Allowlist & Schema Validation
            if tool_name not in TOOL_REGISTRY:
                step_record["status"] = "FAILED"
                step_record["error"] = f"Tool '{tool_name}' rejected: not in approved tool registry."
                execution_log.append(step_record)
                return self._finalize_report(goal, execution_log, failed_step=step_id)

            tool_meta = TOOL_REGISTRY[tool_name]
            required_args = tool_meta.get("required_args", [])
            missing_args = [arg for arg in required_args if arg not in args]
            if missing_args:
                step_record["status"] = "FAILED"
                step_record["error"] = f"Missing required arguments: {missing_args}"
                execution_log.append(step_record)
                return self._finalize_report(goal, execution_log, failed_step=step_id)

            # 2. Safety & Human Confirmation for Destructive Actions
            if tool_meta.get("destructive", False):
                action_desc = f"{tool_name} with parameters {args}"
                confirmed = self.confirm_callback(action_desc)
                if not confirmed:
                    step_record["status"] = "ABORTED"
                    step_record["error"] = "Action rejected by user confirmation."
                    execution_log.append(step_record)
                    return self._finalize_report(goal, execution_log, failed_step=step_id)

            # 3. Invocation with Timeout Protection
            func = tool_meta["function"]
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(func, **args)
                    result = future.result(timeout=self.step_timeout_seconds)
                step_record["output"] = str(result)
            except concurrent.futures.TimeoutError:
                step_record["status"] = "FAILED"
                step_record["error"] = f"Execution timed out after {self.step_timeout_seconds} seconds."
                execution_log.append(step_record)
                return self._finalize_report(goal, execution_log, failed_step=step_id)
            except Exception as ex:
                step_record["status"] = "FAILED"
                step_record["error"] = f"Execution error: {str(ex)}"
                execution_log.append(step_record)
                return self._finalize_report(goal, execution_log, failed_step=step_id)

            # 4. Independent Verification
            verifier = tool_meta.get("verifier")
            if verifier:
                time.sleep(0.5)  # Brief buffer for OS file flush or process spin-up
                try:
                    verified, v_msg = verifier(**args)
                    step_record["verification"] = v_msg
                    if not verified:
                        step_record["status"] = "FAILED"
                        step_record["error"] = f"Verification failed: {v_msg}"
                        execution_log.append(step_record)
                        return self._finalize_report(goal, execution_log, failed_step=step_id)
                except Exception as vex:
                    step_record["status"] = "FAILED"
                    step_record["error"] = f"Verification routine encountered error: {str(vex)}"
                    execution_log.append(step_record)
                    return self._finalize_report(goal, execution_log, failed_step=step_id)

            step_record["status"] = "SUCCESS"
            execution_log.append(step_record)

        return self._finalize_report(goal, execution_log, failed_step=None)

    @staticmethod
    def _finalize_report(goal: str, logs: List[Dict[str, Any]], failed_step: Optional[int]) -> Dict[str, Any]:
        """Produce final summary of completed and failed actions."""
        total = len(logs)
        succeeded = sum(1 for item in logs if item["status"] == "SUCCESS")
        
        if failed_step is None:
            summary = f"Task completed successfully: All {succeeded} steps verified."
            is_successful = True
        else:
            failed_log = logs[-1]
            summary = (f"Task halted at step {failed_step}: {failed_log['tool']} failed. "
                       f"Reason: {failed_log['error']}. ({succeeded}/{total} steps succeeded).")
            is_successful = False

        return {
            "success": is_successful,
            "goal": goal,
            "summary": summary,
            "steps_completed": succeeded,
            "total_steps": total,
            "logs": logs
        }