#!/usr/bin/env python3
"""KnowledgeTool state helper.

This script creates external learning folders, finds existing progress, and
records assessment summaries. It never writes user learning content inside the
plugin source tree.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path.home() / ".knowledge-tool" / "config.json"
DEFAULT_CONFIG: dict[str, Any] = {
    "default_learning_root": None,
    "recent_limit": 10,
    "assessment_difficulty": "adaptive",
    "assessment_order_bias": "avoid",
    "response_mode": "fast",
    "context_policy": "compact",
    "language": "zh-CN",
    "project_scan_max_files": 200,
}

DOC_FILES = {
    "README.md": "# {topic}\n\nStatus: {status}\n\nNext step: {next_step}\n",
    "progress-index.md": "# Progress Index\n\n## Current Position\n\n- Current step: {status}\n- Next step: {next_step}\n\n## Fast Resume Notes\n\nRead this file first when resuming. Use it to avoid reloading long history unless the current step requires it.\n",
    "context-summary.md": "# Context Summary\n\n## Stable Learner Model\n\n## Current Concept\n\n## Recent Scores\n\n## Open Questions\n",
    "interview.md": "# Learner Interview\n\n## Goal\n\n## Current Level\n\n## Constraints\n\n## Practice Environment\n",
    "research-brief.md": "# Research Brief\n\n## Five Perspectives\n\n## Conflict Map\n\n## Integrated Brief\n\n## Peer Review\n",
    "learning-path.md": "# Learning Path\n\n## Resource Triage\n\n## Learning Ladder\n\n## One-Week Route\n",
    "assessment.md": "# Assessment\n\n## Diagnostic Questions\n\n## Assessment Design Notes\n\nAvoid answer-order clues. Shuffle or vary choices, scenarios, and category mappings so learners cannot answer by repeating the order of concepts shown before the question. Avoid count-matching clues too: do not habitually make scenario count equal answer-choice count; reuse answers, add plausible distractors, or include a depends/none option when useful.\n\nAfter each learner answer, record the canonical answer, score, correct points, corrections, and the next focused task. For scenario questions, write the assumptions that determine the answer, such as whether an event may be dropped, buffered, consumed once, or broadcast.\n\n## Retrieval Practice Log\n",
    "feynman-log.md": "# Feynman Loop\n\n## Weak Concepts\n\n## Teach-Back Attempts\n",
    "cheatsheet.md": "# One-Page Cheat Sheet\n\n## Definition\n\n## Core Ideas\n\n## Examples\n\n## Checklist\n\n## Rapid Q&A\n",
}

PROJECT_DOC_FILES = {
    "project-map.md": "# Project Map\n\n## Overview\n\n## Important Files\n\n## Learning Order\n",
    "architecture-notes.md": "# Architecture Notes\n\n## Runtime Shape\n\n## Data Flow\n\n## Extension Points\n",
    "hands-on-tasks.md": "# Hands-On Tasks\n\n## Small Tasks\n\n## Final Project\n",
}

EXCLUDE_DIRS = {
    ".git",
    ".gradle",
    ".idea",
    ".vscode",
    "node_modules",
    "build",
    "dist",
    "out",
    "target",
    ".venv",
    "venv",
    "__pycache__",
}

IMPORTANT_FILE_NAMES = {
    "readme.md",
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "gradle.properties",
    "requirements.txt",
    "pyproject.toml",
    "cargo.toml",
    "go.mod",
    "makefile",
    "dockerfile",
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_config() -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as fh:
            loaded = json.load(fh)
        if isinstance(loaded, dict):
            config.update({k: v for k, v in loaded.items() if k in config})
    return config


def ensure_config() -> Path:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        with CONFIG_PATH.open("w", encoding="utf-8") as fh:
            json.dump(DEFAULT_CONFIG, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    return CONFIG_PATH


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def slugify(value: str, prefix: str | None = None) -> str:
    ascii_slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    ascii_slug = re.sub(r"-+", "-", ascii_slug)
    if not ascii_slug:
        digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
        ascii_slug = f"topic-{digest}"
    if prefix and not ascii_slug.startswith(f"{prefix}-"):
        ascii_slug = f"{prefix}-{ascii_slug}"
    return ascii_slug[:96].strip("-")


def resolve_learning_root(root: str | None) -> Path:
    config = load_config()
    selected = root or config.get("default_learning_root")
    if selected:
        learning_root = Path(os.path.expanduser(str(selected))).resolve()
    else:
        learning_root = (Path.cwd() / ".knowledge-tool" / "learning").resolve()
    try:
        learning_root.relative_to(PLUGIN_ROOT)
    except ValueError:
        return learning_root
    raise SystemExit(
        f"Refusing to write learning content inside plugin source: {learning_root}"
    )


def read_state(path: Path) -> dict[str, Any] | None:
    state_path = path / "learning_state.json"
    if not state_path.exists():
        return None
    try:
        with state_path.open("r", encoding="utf-8") as fh:
            state = json.load(fh)
        if isinstance(state, dict):
            state["_state_path"] = str(state_path)
            state["_learning_dir"] = str(path)
            return state
    except json.JSONDecodeError:
        return None
    return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def update_progress_index(learning_dir: Path, state: dict[str, Any]) -> None:
    mastery = state.get("mastery", [])
    latest = mastery[-1] if mastery else None
    latest_lines = ""
    if latest:
        weak = latest.get("weak_concepts") or []
        if isinstance(weak, list):
            weak_text = "; ".join(str(item) for item in weak) or "None recorded"
        else:
            weak_text = str(weak)
        latest_lines = (
            f"- Latest stage: {latest.get('stage')}\n"
            f"- Latest score: {latest.get('score')}\n"
            f"- Weak concepts: {weak_text}\n"
            f"- Latest next task: {latest.get('next_task')}\n"
        )
    else:
        latest_lines = "- No assessment recorded yet.\n"

    content = (
        "# Progress Index\n\n"
        "## Current Position\n\n"
        f"- Topic: {state.get('topic')}\n"
        f"- Mode: {state.get('mode')}\n"
        f"- Current step: {state.get('current_step')}\n"
        f"- Next step: {state.get('next_step')}\n"
        f"- Updated at: {state.get('updated_at')}\n\n"
        "## Latest Assessment\n\n"
        f"{latest_lines}\n"
        "## Fast Resume Protocol\n\n"
        "1. Read `learning_state.json` and this file first.\n"
        "2. Read only the current-stage Markdown file unless the learner asks for a broader review.\n"
        "3. Prefer a concise answer plus one focused retrieval question.\n"
        "4. Update this index after scoring, changing stage, or setting the next task.\n"
    )
    (learning_dir / "progress-index.md").write_text(content, encoding="utf-8")


def project_summary(project_path: Path, max_files: int) -> dict[str, Any]:
    files: list[str] = []
    important: list[str] = []
    for root, dirs, names in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        rel_root = Path(root).relative_to(project_path)
        for name in sorted(names):
            rel = (rel_root / name).as_posix() if str(rel_root) != "." else name
            files.append(rel)
            if name.lower() in IMPORTANT_FILE_NAMES:
                important.append(rel)
            if len(files) >= max_files:
                return {
                    "project_path": str(project_path),
                    "files_sample": files,
                    "important_files": important,
                    "truncated": True,
                }
    return {
        "project_path": str(project_path),
        "files_sample": files,
        "important_files": important,
        "truncated": False,
    }


def init_learning(args: argparse.Namespace) -> dict[str, Any]:
    learning_root = resolve_learning_root(args.root)
    learning_root.mkdir(parents=True, exist_ok=True)

    topic = args.topic.strip()
    mode = args.mode
    project_path = None
    summary = None
    slug_prefix = None
    if mode == "project":
        if not args.project_path:
            raise SystemExit("--project-path is required for project mode")
        project_path = Path(args.project_path).expanduser().resolve()
        if not project_path.exists():
            raise SystemExit(f"Project path does not exist: {project_path}")
        if not topic:
            topic = project_path.name
        slug_prefix = "project"
        summary = project_summary(project_path, load_config()["project_scan_max_files"])

    slug = args.slug or slugify(topic, slug_prefix)
    learning_dir = (learning_root / slug).resolve()
    learning_dir.mkdir(parents=True, exist_ok=True)

    state_path = learning_dir / "learning_state.json"
    existing = read_state(learning_dir)
    created_at = existing.get("created_at") if existing else now_iso()
    state = existing or {}
    state.update(
        {
            "topic": topic,
            "slug": slug,
            "mode": mode,
            "learning_root": str(learning_root),
            "learning_dir": str(learning_dir),
            "project_path": str(project_path) if project_path else None,
            "current_step": state.get("current_step", "learner_interview"),
            "completed_steps": state.get("completed_steps", []),
            "mastery": state.get("mastery", []),
            "next_step": state.get(
                "next_step",
                "Run the learner interview and create diagnostic questions.",
            ),
            "created_at": created_at,
            "updated_at": now_iso(),
        }
    )
    if summary:
        state["project_scan"] = summary
    state.pop("_state_path", None)
    state.pop("_learning_dir", None)
    write_json(state_path, state)

    for filename, template in DOC_FILES.items():
        write_if_missing(
            learning_dir / filename,
            template.format(
                topic=topic,
                status=state["current_step"],
                next_step=state["next_step"],
            ),
        )
    if mode == "project":
        for filename, template in PROJECT_DOC_FILES.items():
            write_if_missing(learning_dir / filename, template)
    update_progress_index(learning_dir, state)

    return result_payload("initialized", learning_dir, state)


def all_states(root: Path) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    states: list[dict[str, Any]] = []
    for state_path in root.glob("*/learning_state.json"):
        state = read_state(state_path.parent)
        if state:
            states.append(state)
    states.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return states


def continue_learning(args: argparse.Namespace) -> dict[str, Any]:
    learning_root = resolve_learning_root(args.root)
    states = all_states(learning_root)
    if not states:
        return {
            "status": "not_found",
            "learning_root": str(learning_root),
            "message": "No learning_state.json files were found.",
        }

    query = (args.query or "").strip()
    if not query:
        state = states[0]
        return result_payload("resume_latest", Path(state["_learning_dir"]), state)

    normalized_query = normalize_text(query)
    exact: list[dict[str, Any]] = []
    fuzzy: list[dict[str, Any]] = []
    for state in states:
        slug = state.get("slug", "")
        topic = state.get("topic", "")
        normalized_slug = normalize_text(slug)
        normalized_topic = normalize_text(topic)
        if normalized_query in {normalized_slug, normalized_topic}:
            exact.append(state)
        elif normalized_query in normalized_slug or normalized_query in normalized_topic:
            fuzzy.append(state)

    matches = exact or fuzzy
    if len(matches) == 1:
        return result_payload("resume_match", Path(matches[0]["_learning_dir"]), matches[0])
    if len(matches) > 1:
        return {
            "status": "multiple_matches",
            "learning_root": str(learning_root),
            "candidates": [candidate_summary(item) for item in matches[:10]],
        }
    return {
        "status": "not_found",
        "learning_root": str(learning_root),
        "query": query,
        "message": "No matching learning topic was found.",
    }


def record_assessment(args: argparse.Namespace) -> dict[str, Any]:
    learning_root = resolve_learning_root(args.root)
    learning_dir = (learning_root / args.slug).resolve()
    state = read_state(learning_dir)
    if not state:
        raise SystemExit(f"No learning_state.json found for slug: {args.slug}")

    entry = {
        "recorded_at": now_iso(),
        "stage": args.stage,
        "score": args.score,
        "weak_concepts": args.weak_concepts or [],
        "next_task": args.next_task,
    }
    mastery = state.get("mastery", [])
    mastery.append(entry)
    state["mastery"] = mastery
    state["updated_at"] = now_iso()
    state["next_step"] = args.next_task
    state["current_step"] = args.stage
    state.pop("_state_path", None)
    state.pop("_learning_dir", None)
    write_json(learning_dir / "learning_state.json", state)
    update_progress_index(learning_dir, state)
    return result_payload("assessment_recorded", learning_dir, state)


def candidate_summary(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "topic": state.get("topic"),
        "slug": state.get("slug"),
        "mode": state.get("mode"),
        "learning_dir": state.get("_learning_dir") or state.get("learning_dir"),
        "updated_at": state.get("updated_at"),
        "current_step": state.get("current_step"),
        "next_step": state.get("next_step"),
    }


def result_payload(status: str, learning_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    files = sorted(
        str(path)
        for path in learning_dir.iterdir()
        if path.is_file() and path.name != "learning_state.json"
    )
    return {
        "status": status,
        "learning_dir": str(learning_dir),
        "state_path": str(learning_dir / "learning_state.json"),
        "state": candidate_summary(
            {
                **state,
                "_learning_dir": str(learning_dir),
            }
        ),
        "files": files,
    }


def show_config(args: argparse.Namespace) -> dict[str, Any]:
    if args.init:
        ensure_config()
    return {
        "status": "config",
        "config_path": str(CONFIG_PATH),
        "config": load_config(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="KnowledgeTool state helper")
    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init", help="Create or update a learning folder")
    init_cmd.add_argument("--topic", required=True)
    init_cmd.add_argument("--mode", choices=["topic", "project"], default="topic")
    init_cmd.add_argument("--project-path")
    init_cmd.add_argument("--root")
    init_cmd.add_argument("--slug")
    init_cmd.set_defaults(func=init_learning)

    cont = sub.add_parser("continue", help="Find a learning folder to resume")
    cont.add_argument("--query")
    cont.add_argument("--root")
    cont.set_defaults(func=continue_learning)

    assess = sub.add_parser("assess", help="Record a mastery assessment summary")
    assess.add_argument("--slug", required=True)
    assess.add_argument("--stage", required=True)
    assess.add_argument("--score", type=float, required=True)
    assess.add_argument("--weak-concepts", action="append")
    assess.add_argument("--next-task", required=True)
    assess.add_argument("--root")
    assess.set_defaults(func=record_assessment)

    config = sub.add_parser("config", help="Show or initialize configuration")
    config.add_argument("--init", action="store_true")
    config.set_defaults(func=show_config)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    payload = args.func(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
