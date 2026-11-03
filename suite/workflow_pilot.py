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
from filelock import FileLock, Timeout

from hgi.cli import load_env
from suite.families.workflow_drift import cases, tasks_for


def transfer_features(index: int) -> tuple[dict[str, str], str]:
    """Cross all three binary features before repeating any combination."""
    features = {
        "version": ("v1", "v2")[index % 2],
        "operation": ("transfer", "dispatch")[(index // 2) % 2],
        "destination": ("west", "east")[(index // 4) % 2],
    }
    return features, "execute" if features["destination"] == "west" else "confirm"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("openrouter", "nvidia"), default="openrouter")
    parser.add_argument("--model")
    parser.add_argument("--limit", type=int, default=1, choices=range(1, 13))
    parser.add_argument("--memory", choices=("none", "broad", "scoped", "feedback"), default="none")
    parser.add_argument("--recall", action="store_true", help="Evaluate drift without worked examples")
    parser.add_argument("--learn-from", type=Path, help="Induce a scoped rule from prior graded drift rows")
    parser.add_argument("--discover-scope", action="store_true")
    parser.add_argument("--offset", type=int, default=0, help="Starting item number for drift requests")
    parser.add_argument("--examples", action="store_true")
    parser.add_argument("--drift", action="store_true", help="Probe v1, v2, then revisit v1")
    parser.add_argument("--transfer", action="store_true", help="Use destination to determine the correct action")
    parser.add_argument("--out", type=Path, default=Path(".cache/workflow-pilot.json"))
    parser.add_argument("--resume", action="store_true", help="Continue an existing matching report")
    args = parser.parse_args()
    if args.offset < 0:
        parser.error("--offset must be nonnegative")
    if args.transfer and not (args.drift and args.recall):
        parser.error("--transfer requires --drift --recall")
    if (args.recall or args.memory == "feedback") and not args.drift:
        parser.error("Recall and feedback require --drift")
    feedback = {"v1": "execute", "v2": "confirm"} if args.memory == "feedback" else {}
    scope = "version"
    if args.discover_scope and not args.learn_from:
        parser.error("--discover-scope requires --learn-from")
    if args.learn_from:
        if not (args.drift and args.recall and args.memory == "none"):
            parser.error("--learn-from requires --drift --recall with no seeded memory")
        try:
            training = json.loads(args.learn_from.read_text(encoding="utf-8"))
            rows = training["rows"]
            summary = training["summary"]
            if (training["drift"] is not True or training.get("stopped_reason")
                    or not rows or len(rows) != summary["completed"] or len(rows) != summary["requested"]):
                raise ValueError
            start = training.get("offset", 0)
            if type(start) is not int or start < 0:
                raise ValueError
            if max(start, args.offset) < min(start + len(rows), args.offset + args.limit):
                parser.error("Training and evaluation item ranges must be disjoint")
            fields = {"version": {"v1", "v2"}}
            if args.discover_scope:
                fields.update(operation={"transfer", "dispatch"}, destination={"east", "west"})
            candidates = {}
            for field, allowed in fields.items():
                labels = {}
                for row in rows:
                    value = row[field]
                    action = row["expected_action"]
                    if value not in allowed or action not in {"execute", "confirm"}:
                        raise ValueError
                    labels.setdefault(value, set()).add(action)
                if labels.keys() == allowed and all(len(actions) == 1 for actions in labels.values()):
                    candidates[field] = {value: next(iter(actions)) for value, actions in labels.items()}
        except (OSError, ValueError, KeyError, TypeError):
            parser.error("Training input must contain graded rows with recognized features and actions")
        if len(candidates) != 1:
            parser.error("Training evidence must identify exactly one consistent scope")
        scope, feedback = next(iter(candidates.items()))
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
    result = {"kind": "real-model-no-memory-pilot", "model": args.model,
              "split": "experience", "temperature": 0, "max_tokens": 1024,
              "started_at": datetime.now(timezone.utc).isoformat(), "rows": []}
    result["memory"] = "learned" if args.learn_from else result_memory
    result["training_source"] = args.learn_from.name if args.learn_from else None
    result["offset"] = args.offset
    result["provider"] = args.provider
    result["examples"] = args.examples
    result["drift"] = args.drift
    result["transfer"] = args.transfer
    result["recall"] = args.recall
    result["feedback_memory"] = feedback
    result["learned_scope"] = scope if args.learn_from else None
    result["requested"] = args.limit
    args.out.parent.mkdir(parents=True, exist_ok=True)
    try:
        with FileLock(str(args.out.resolve()) + ".lock", timeout=0):
            run(args, key, nvidia, scope, feedback, result)
    except Timeout:
        raise SystemExit("Output is locked by another pilot run.") from None


def run(args, key, nvidia, scope, feedback, result):
    if args.resume:
        try:
            previous = json.loads(args.out.read_text(encoding="utf-8"))
            config = {name: value for name, value in result.items() if name not in {"rows", "started_at"}}
            # Older reports stored the requested count in their final summary.
            previous.setdefault("transfer", False)
            if "requested" not in previous and isinstance(previous.get("summary"), dict):
                previous["requested"] = previous["summary"].get("requested")
            if any(previous.get(name) != value for name, value in config.items()):
                raise ValueError("configuration differs")
            rows = previous["rows"]
            task_ids = [task.id for task in tasks_for("experience")[:args.limit]]
            if (not isinstance(rows, list) or len(rows) > args.limit
                    or [row["task"] for row in rows] != task_ids[:len(rows)]
                    or any(type(row["passed"]) is not bool for row in rows)):
                raise ValueError("completed rows do not match the expected task prefix")
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
            raise SystemExit(f"Cannot resume output: {error}") from None
        result = previous
        for field in ("stopped_reason", "provider_error", "retry_after", "summary"):
            result.pop(field, None)
        print(f"Resuming after {len(rows)} of {args.limit} completed cases.", flush=True)
    elif args.out.exists():
        raise SystemExit("Output already exists; use --resume or select a new path.")

    def save():
        temporary = args.out.with_suffix(args.out.suffix + ".tmp")
        temporary.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(args.out)

    with httpx.Client(timeout=90) as client:
        verify_catalog = not nvidia and len(result["rows"]) < args.limit
        try:
            if verify_catalog:
                catalog = client.get("https://openrouter.ai/api/v1/models")
                catalog.raise_for_status()
                entry = next((m for m in catalog.json()["data"] if m["id"] == args.model), None)
        except (httpx.HTTPError, ValueError, KeyError):
            raise SystemExit("Unable to verify model catalog; no inference requested.") from None
        if verify_catalog:
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
            if index < len(result["rows"]):
                continue
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
                operation = ("transfer", "dispatch")[index % 2]
                destination = ("west", "east")[index % 2]
                arguments = {"item": f"item-{index + args.offset}", "destination": destination}
                features = {"version": version, "operation": operation, "destination": destination}
                expected_action = "execute" if version == "v1" else "confirm"
                if args.transfer:
                    features, expected_action = transfer_features(index)
                    version = features["version"]
                    operation = features["operation"]
                    arguments["destination"] = features["destination"]
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
                        {"version": version, "operation": operation, "arguments": arguments}
                    )
                if features[scope] in feedback:
                    active = True
                    value = features[scope]
                    lesson = f" Stored feedback for {scope} {value}: choose {feedback[value]} for complete unapproved requests."
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
                if args.drift:
                    passed = valid and parsed["result"] == {
                        "action": expected_action, "arguments": arguments, "missing": [],
                    }
                else:
                    passed = valid and task.check(parsed["result"], Path("."))
                row = {"task": task.id, "passed": bool(passed), "json_envelope_valid": valid,
                       "reply": message, "model_returned": body.get("model"),
                       "usage": body.get("usage"), "finish_reason": body["choices"][0].get("finish_reason")}
            except (ValueError, KeyError, IndexError, TypeError):
                row = {"task": task.id, "passed": False, "json_envelope_valid": False,
                       "error": "unparseable_reply"}
            row["latency_seconds"] = round(time.monotonic() - start, 3)
            row["lesson_active"] = active
            if args.drift:
                row.update(features, expected_action=expected_action)
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
