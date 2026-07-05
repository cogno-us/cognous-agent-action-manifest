"""
CLI for Agent Action Manifest.

Entry point: aam
"""

from __future__ import annotations

import glob as _glob
import json
import sys
from pathlib import Path


def _load_or_exit(path_str: str):
    """Load a manifest, printing an error and exiting with code 2 on failure."""
    from .loader import ManifestLoadError, load_manifest

    try:
        return load_manifest(path_str)
    except ManifestLoadError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)


def _cmd_validate(args: list[str]) -> int:
    if len(args) != 1:
        print("Usage: aam validate <manifest.json>", file=sys.stderr)
        return 2

    manifest = _load_or_exit(args[0])

    from .validator import validate_manifest

    report = validate_manifest(manifest)

    status = "VALID" if report.valid else "INVALID"
    print(f"Validation result: {status}")
    print(f"Manifest ID:       {report.manifest_id}")

    errors = [i for i in report.issues if i.severity.value == "error"]
    warnings = [i for i in report.issues if i.severity.value == "warning"]

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for issue in errors:
            loc = f" [{issue.path}]" if issue.path else ""
            print(f"  [{issue.code}]{loc} {issue.message}")

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for issue in warnings:
            loc = f" [{issue.path}]" if issue.path else ""
            print(f"  [{issue.code}]{loc} {issue.message}")

    if not report.issues:
        print("No issues found.")

    return 0 if report.valid else 1


def _cmd_summarize(args: list[str]) -> int:
    if len(args) != 1:
        print("Usage: aam summarize <manifest.json>", file=sys.stderr)
        return 2

    manifest = _load_or_exit(args[0])

    from collections import Counter

    type_counts: Counter = Counter(a.action_type.value for a in manifest.actions)
    posture_counts: Counter = Counter(
        (a.default_action or manifest.default_action).value for a in manifest.actions
    )

    n_authority = sum(1 for a in manifest.actions if a.authority_required)
    n_review = sum(
        1
        for a in manifest.actions
        if a.review_requirement and a.review_requirement.mode.value != "none"
    )
    n_reliance = sum(
        1
        for a in manifest.actions
        if a.reliance_requirement and a.reliance_requirement.required
    )
    n_sensitive = sum(
        1
        for a in manifest.actions
        if a.payload_policy and a.payload_policy.sensitive_fields
    )

    print(f"Manifest ID:          {manifest.manifest_id}")
    print(f"Agent name:           {manifest.agent_name}")
    print(f"Environment:          {manifest.environment}")
    print(f"Tools:                {len(manifest.tools)}")
    print(f"Actions:              {len(manifest.actions)}")

    print("\nActions by type:")
    for action_type, count in sorted(type_counts.items()):
        print(f"  {action_type}: {count}")

    print("\nActions by default posture:")
    for posture, count in sorted(posture_counts.items()):
        print(f"  {posture}: {count}")

    print(f"\nActions requiring authority: {n_authority}")
    print(f"Actions requiring review:    {n_review}")
    print(f"Actions requiring reliance:  {n_reliance}")
    print(f"Actions with sensitive fields: {n_sensitive}")

    return 0


def _cmd_list_actions(args: list[str]) -> int:
    if len(args) != 1:
        print("Usage: aam list-actions <manifest.json>", file=sys.stderr)
        return 2

    manifest = _load_or_exit(args[0])

    col_widths = {
        "action_name": max((len(a.action_name) for a in manifest.actions), default=11),
        "tool_name": max((len(a.tool_name) for a in manifest.actions), default=9),
        "action_type": max((len(a.action_type.value) for a in manifest.actions), default=11),
        "posture": 8,
        "authority": 12,
        "review": 10,
    }
    col_widths["action_name"] = max(col_widths["action_name"], 11)
    col_widths["tool_name"] = max(col_widths["tool_name"], 9)
    col_widths["action_type"] = max(col_widths["action_type"], 11)

    header = (
        f"{'action_name':<{col_widths['action_name']}}  "
        f"{'tool_name':<{col_widths['tool_name']}}  "
        f"{'action_type':<{col_widths['action_type']}}  "
        f"{'posture':<{col_widths['posture']}}  "
        f"{'authority_scopes':<30}  "
        f"{'review_mode'}"
    )
    print(header)
    print("-" * len(header))

    for action in manifest.actions:
        effective = (action.default_action or manifest.default_action).value
        scopes = ", ".join(a.scope for a in action.authority_required) or "(none)"
        review = (
            action.review_requirement.mode.value
            if action.review_requirement
            else "none"
        )
        row = (
            f"{action.action_name:<{col_widths['action_name']}}  "
            f"{action.tool_name:<{col_widths['tool_name']}}  "
            f"{action.action_type.value:<{col_widths['action_type']}}  "
            f"{effective:<{col_widths['posture']}}  "
            f"{scopes:<30}  "
            f"{review}"
        )
        print(row)

    return 0


def _cmd_check_examples(args: list[str]) -> int:
    pattern = str(Path("examples") / "*.manifest.json")
    files = sorted(_glob.glob(pattern))

    if not files:
        print("No example manifests found matching examples/*.manifest.json", file=sys.stderr)
        return 2

    from .loader import ManifestLoadError, load_manifest
    from .validator import validate_manifest

    all_valid = True
    for fpath in files:
        try:
            manifest = load_manifest(fpath)
        except ManifestLoadError as exc:
            print(f"LOAD ERROR  {fpath}: {exc}")
            all_valid = False
            continue

        report = validate_manifest(manifest)
        errors = [i for i in report.issues if i.severity.value == "error"]
        if errors:
            print(f"INVALID     {fpath} ({len(errors)} error(s))")
            for issue in errors:
                print(f"  [{issue.code}] {issue.message}")
            all_valid = False
        else:
            warnings = [i for i in report.issues if i.severity.value == "warning"]
            print(f"VALID       {fpath} ({len(warnings)} warning(s))")

    return 0 if all_valid else 1


def main() -> None:
    argv = sys.argv[1:]

    if not argv:
        print(
            "Usage: aam <command> [args]\n"
            "Commands:\n"
            "  validate <manifest.json>\n"
            "  summarize <manifest.json>\n"
            "  list-actions <manifest.json>\n"
            "  check-examples",
            file=sys.stderr,
        )
        sys.exit(2)

    command = argv[0]
    rest = argv[1:]

    commands = {
        "validate": _cmd_validate,
        "summarize": _cmd_summarize,
        "list-actions": _cmd_list_actions,
        "check-examples": _cmd_check_examples,
    }

    if command not in commands:
        print(f"Unknown command: '{command}'", file=sys.stderr)
        print(f"Available commands: {', '.join(commands)}", file=sys.stderr)
        sys.exit(2)

    exit_code = commands[command](rest)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
