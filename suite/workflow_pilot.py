"""Free-only, sequential OpenRouter action-selection pilot (not HGI learning)."""

from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import httpx

from hgi.cli import load_env
from suite.families.workflow_drift import cases, tasks_for


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("openrouter", "nvidia"), default="openrouter")
    parser.add_argument("--model")
    parser.add_argument("--limit", type=int, default=1, choices=range(1, 13))
    parser.add_argument("--memory", choices=("none", "broad", "scoped", "feedback"), default="none")
    parser.add_argument("--recall", action="store_true", help="Evaluate drift without worked examples")
    parser.add_argument("--examples", action="store_true")
    parser.add_argument("--drift", action="store_true", help="Probe v1, v2, then revisit v1")
    parser.add_argument("--out", type=Path, default=Path(".cache/workflow-pilot.json"))
    args = parser.parse_args()
    if (args.recall or args.memory == "feedback") and not args.drift:
        parser.error("Recall and feedback require --drift")
    feedback = {"v1": "execute", "v2": "confirm"} if args.memory == "feedback" else {}
    result_memory = args.memory
    load_env()
    nvidia = args.provider == "nvidia"
    nvidia_model = "nvidia/nemotron-3.5-super-vl-120b-a12b"
    args.model = args.model or (nvidia_model if nvidia else "liquid/lfm-2.5-2.6b:free")
    key_name = "NVIDIA_API_KEY" if nvidia else "HGI_INFERENCE_API_KEY"
    key = os.getenv(key_name)
    if not key:
        raise SystemExit(f"Configure {key_name} locally first.")
    if (nvidia and args.model != nvidia_model) or (not nvidia and not args.model.endswith(":free")):
        raise SystemExit("Only explicitly free model IDs are allowed.")
    if args.out.exists():
        raise SystemExit("Output already exists; select a new path to preserve the earlier run.")
    result = {"kind": "real-model-no-memory-pilot", "model": args.model,
              "split": "experience", "temperature": 0, "max_tokens": 1024,
              "started_at": datetime.now(timezone.utc).isoformat(), "rows": []}
    result["memory"] = result_memory
    result["provider"] = args.provider
    result["examples"] = args.examples
    result["drift"] = args.drift
    result["recall"] = args.recall
    result["feedback_memory"] = feedback
    args.out.parent.mkdir(parents=True, exist_ok=True)

    def save():
        args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    with httpx.Client(timeout=90) as client:
        try:
            if not nvidia:
                catalog = client.get("https://openrouter.ai/api/v1/models")
                catalog.raise_for_status()
                entry = next((m for m in catalog.json()["data"] if m["id"] == args.model), None)
        except (httpx.HTTPError, ValueError, KeyError):
            raise SystemExit("Unable to verify model catalog; no inference requested.") from None
        if not nvidia:
            if not entry or any(float(entry["pricing"][k]) != 0 for k in ("prompt", "completion")):
                raise SystemExit("Selected model is unavailable or not zero-priced; stopping.")
            result["catalog_entry"] = entry
        endpoint = ("https://integrate.api.nvidia.com/v1/chat/completions" if nvidia
                    else "https://openrouter.ai/api/v1/chat/completions")
        options = {} if nvidia else {
            "provider": {"allow_fallbacks": False},
            "response_format": {"type": "json_object"},
        }
        save()
        for index, (task, case) in enumerate(zip(tasks_for("experience")[:args.limit], cases("experience"))):
            active = args.memory == "broad" or (
                args.memory == "scoped" and bool(set(case.required) - case.supplied.keys())
            )
            lesson = " Stored lesson: always ask for clarification before acting." if active else ""
            prompt = task.prompt
            expected_action = None
            version = None
            if args.examples:
                examples = cases("selection")[:6]
                demonstrations = [
                    {"required": example.required, "supplied": example.supplied,
                     "confirmation_required": example.confirmation_required,
                     "user_confirmed": example.confirmed, "result": example.expected()}
                    for example in examples
                ]
                prompt = ("Infer the current workflow from these examples: "
                          + json.dumps(demonstrations)
                          + "\nReturn the result for this new request: "
                          + task.prompt.split(" Request: ", 1)[1])
            if args.drift:
                version = ("v1", "v2", "v2", "v1")[index % 4]
                arguments = {"item": f"item-{index}", "destination": "west"}
                expected_action = "execute" if version == "v1" else "confirm"
                active = args.memory == "broad" or (args.memory == "scoped" and version == "v1")
                lesson = " Stored workflow lesson: execute complete requests without asking for approval." if active else ""
                prompt = (
                    'Infer the workflow from these examples. A complete request in v1 returned '
                    '{"action":"execute","arguments":{"item":"sample","destination":"east"},"missing":[]}. '
                    'A complete, unapproved request in v2 returned '
                    '{"action":"confirm","arguments":{"item":"sample","destination":"east"},"missing":[]}. '
                    "Give the next action for this complete, unapproved request: "
                    + json.dumps({"version": version, "arguments": arguments})
                )
                if args.recall:
                    prompt = "Choose the next action for this complete, unapproved request: " + json.dumps(
                        {"version": version, "arguments": arguments}
                    )
                if version in feedback:
                    active = True
                    lesson = f" Stored feedback for {version}: choose {feedback[version]} for complete unapproved requests."
            if result["rows"]:
                time.sleep(4)
            start = time.monotonic()
            try:
                response = client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {key}"},
                    json={"model": args.model, "temperature": 0, "max_tokens": 1024,
                          **options,
                          "messages": [
                              {"role": "system", "content": "Return only JSON matching the supplied output schema." + lesson},
                              {"role": "user", "content": prompt + "\nSchema: " + json.dumps(task.schema)},
                          ]},
                )
            except httpx.HTTPError:
                result["stopped_reason"] = "transport_error"
                save()
                break
            if response.status_code != 200:
                result["stopped_reason"] = f"http_{response.status_code}"
                try:
                    error = response.json().get("error", {})
                    result["provider_error"] = str(error.get("message", "" )).replace(key, "[redacted]")[:1500]
                except (ValueError, AttributeError):
                    result["provider_error"] = "Non-JSON error response"
                result["retry_after"] = response.headers.get("retry-after")
                save()
                print(result["provider_error"], flush=True)
                break
            try:
                body = response.json()
                message = body["choices"][0]["message"].get("content")
                parsed = json.loads(message) if isinstance(message, str) else None
                valid = isinstance(parsed, dict) and set(parsed) == {"result"}
                passed = valid and task.check(parsed["result"], Path("."))
                if args.drift:
                    passed = valid and parsed["result"] == {
                        "action": expected_action, "arguments": arguments, "missing": [],
                    }
                row = {"task": task.id, "passed": bool(passed), "json_envelope_valid": valid,
                       "reply": message, "model_returned": body.get("model"),
                       "usage": body.get("usage"), "finish_reason": body["choices"][0].get("finish_reason")}
            except (ValueError, KeyError, IndexError, TypeError):
                row = {"task": task.id, "passed": False, "json_envelope_valid": False,
                       "error": "unparseable_reply"}
            row["latency_seconds"] = round(time.monotonic() - start, 3)
            row["lesson_active"] = active
            if args.drift:
                row.update(version=version, expected_action=expected_action)
            result["rows"].append(row)
            save()
            print(f"{task.id}: {'PASS' if row['passed'] else 'FAIL'}", flush=True)
    counts = Counter(row["passed"] for row in result["rows"])
    result["summary"] = {"completed": len(result["rows"]), "passed": counts[True],
                         "failed": counts[False], "requested": args.limit}
    save()
    print(json.dumps(result["summary"]))
    if result.get("stopped_reason"):
        raise SystemExit("Stopped: " + result["stopped_reason"])


if __name__ == "__main__":
    main()
