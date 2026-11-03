"""Compare a fixed scope search with a strategy selected on development tasks."""

import json
import argparse
from pathlib import Path
from itertools import combinations, product


INPUTS = tuple(product((0, 1), repeat=3))


def predict(experience, query, max_width):
    """Use the simplest consistent hypotheses and abstain on disagreement."""
    for width in range(1, max_width + 1):
        predictions = set()
        for fields in combinations(range(3), width):
            table = {}
            for features, action in experience:
                key = tuple(features[i] for i in fields)
                table.setdefault(key, set()).add(action)
            if all(len(actions) == 1 for actions in table.values()):
                key = tuple(query[i] for i in fields)
                predictions.update(table.get(key, {None}))
        if predictions:
            return next(iter(predictions)) if len(predictions) == 1 else None
    return None


def evaluate(rule, max_width, order, trace=None):
    experience = []
    correct = wrong = abstained = 0
    for features in order:
        expected = rule(features)
        predicted = predict(experience, features, max_width)
        if trace is not None:
            trace.append({"features": features, "feedback_seen": len(experience),
                          "prediction": predicted, "expected": expected})
        correct += predicted == expected
        wrong += predicted is not None and predicted != expected
        abstained += predicted is None
        experience.append((features, expected))
    return {"correct": correct, "wrong": wrong, "abstained": abstained}


def report(proposed=None, trace=None):
    development = (
        lambda x: x[0],
        lambda x: x[0] ^ x[1],
    )
    held_out = {
        "single_feature": lambda x: x[2],
        "interaction": lambda x: x[1] ^ x[2],
    }
    # Revisit each input after its initial label has been observed.
    stream = INPUTS + tuple(reversed(INPUTS))
    scores = {
        width: sum(evaluate(rule, width, stream)["correct"] for rule in development)
        for width in (1, 2)
    }
    selected = max(scores, key=lambda width: (scores[width], -width))
    if trace is not None:
        for index, rule in enumerate(development):
            rows = []
            evaluate(rule, 1, stream, rows)
            trace.append({"stream": index, "rows": rows})
    arms = {"fixed": 1, "selected": selected}
    if proposed is not None:
        arms["model_proposed"] = proposed
    contradictory = [(INPUTS[0], 0), (INPUTS[0], 1)]
    return {
        "development_scores": scores,
        "selected_max_width": selected,
        "labels_per_stream": len(stream),
        "held_out": {
            name: {arm: evaluate(rule, width, stream)
                   for arm, width in arms.items()}
            for name, rule in held_out.items()
        },
        "contradictory_feedback_abstention": {
            arm: predict(contradictory, INPUTS[0], width) is None
            for arm, width in arms.items()
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=Path, help="Frozen JSON proposal with max_width")
    parser.add_argument("--development-traces", action="store_true")
    args = parser.parse_args()
    if args.development_traces:
        traces = []
        report(trace=traces)
        print(json.dumps(traces, indent=2))
    else:
        width = None
        if args.proposal:
            width = json.loads(args.proposal.read_text(encoding="utf-8"))["max_width"]
            if type(width) is not int or width not in (1, 2, 3):
                parser.error("Proposal max_width must be an integer from 1 to 3")
        print(json.dumps(report(proposed=width), indent=2))
