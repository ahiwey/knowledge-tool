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
import shutil
import statistics
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(
    os.environ.get(
        "KNOWLEDGE_TOOL_CONFIG",
        str(Path.home() / ".knowledge-tool" / "config.json"),
    )
).expanduser().resolve()
DEFAULT_CONFIG: dict[str, Any] = {
    "default_learning_root": None,
    "confirm_new_topic_root": True,
    "recent_limit": 10,
    "assessment_difficulty": "adaptive",
    "assessment_order_bias": "avoid",
    "question_quality_mode": "strict",
    "response_mode": "fast",
    "context_policy": "compact",
    "session_style": "sprint",
    "progress_report_every": 3,
    "mastery_threshold": 8.0,
    "max_consecutive_remediation_turns": 1,
    "language": "zh-CN",
    "project_scan_max_files": 200,
}

HISTORY_FILENAME = "assessment-history.jsonl"
ROADMAP_FILENAME = "roadmap.json"
RECENT_ASSESSMENT_LIMIT = 10

DOC_FILES = {
    "README.md": "# {topic}\n\nStatus: {status}\n\nNext step: {next_step}\n",
    "progress-index.md": "# Progress Index\n\n## Current Position\n\n- Current step: {status}\n- Next step: {next_step}\n\n## Fast Resume Notes\n\nRead this file first when resuming. Use it to avoid reloading long history unless the current step requires it.\n",
    "context-summary.md": "# Context Summary\n\n## Stable Learner Model\n\n## Current Concept\n\n## Recent Scores\n\n## Open Questions\n",
    "interview.md": "# Learner Interview\n\n## Goal\n\n## Current Level\n\n## Constraints\n\n## Practice Environment\n",
    "research-brief.md": "# Research Brief\n\n## Five Perspectives\n\n## Conflict Map\n\n## Integrated Brief\n\n## Peer Review\n",
    "learning-path.md": "# Learning Path\n\n## Resource Triage\n\n## Learning Ladder\n\n## One-Week Route\n",
    "assessment.md": "# Assessment\n\n## Diagnostic Questions\n\n## Assessment Design Notes\n\nBefore asking, run the question quality gate: test one main concept, state assumptions that change the answer, make the answer shape clear, match difficulty to the learner, and prefer questions where wrong answers reveal useful misconceptions. Use plain language first, then terminology.\n\nPrefer free recall over recognition. Do not provide an answer bank or choices unless the learner asks for them, beginner scaffolding is needed, or the task specifically requires multiple-choice practice.\n\nAvoid answer-order clues. Shuffle or vary choices, scenarios, and category mappings so learners cannot answer by repeating the order of concepts shown before the question. Avoid count-matching clues too: do not habitually make scenario count equal answer-choice count; reuse answers, add plausible distractors, or include a depends/none option when useful.\n\nAfter each learner answer, record the canonical answer, score, correct points, corrections, and the next focused task. For scenario questions, write the assumptions that determine the answer, such as whether an event may be dropped, buffered, consumed once, or broadcast. If the learner flags a question as vague or poorly scaled, record the teaching issue and rewrite the next question.\n\n## Retrieval Practice Log\n",
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


def write_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(CONFIG_PATH, config)


def recommended_learning_root() -> Path:
    documents = Path.home() / "Documents"
    parent = documents if documents.exists() else Path.home()
    return (parent / "KnowledgeTool" / "learning").resolve()


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


def validate_learning_root(learning_root: Path) -> Path:
    learning_root = learning_root.expanduser().resolve()
    if learning_root == PLUGIN_ROOT:
        raise SystemExit(
            f"Refusing to write learning content inside plugin source: {learning_root}"
        )
    try:
        learning_root.relative_to(PLUGIN_ROOT)
    except ValueError:
        return learning_root
    raise SystemExit(
        f"Refusing to write learning content inside plugin source: {learning_root}"
    )


def configured_learning_root() -> Path | None:
    selected = load_config().get("default_learning_root")
    if not selected:
        return None
    return validate_learning_root(Path(os.path.expanduser(str(selected))))


def resolve_learning_root(root: str | None) -> Path:
    if root:
        return validate_learning_root(Path(os.path.expanduser(root)))
    configured = configured_learning_root()
    if configured:
        return configured
    raise SystemExit(
        "No learning root is configured. Run `config --use-recommended-root` "
        "or `config --set-learning-root <path>` after confirming the location."
    )


def storage_confirmation_payload(configured: Path | None = None) -> dict[str, Any]:
    return {
        "status": (
            "needs_new_topic_root_confirmation"
            if configured
            else "needs_storage_confirmation"
        ),
        "config_path": str(CONFIG_PATH),
        "recommended_learning_root": str(recommended_learning_root()),
        "configured_learning_root": str(configured) if configured else None,
        "message": (
            "Ask the learner where to save this new topic. Offer the configured "
            "root first when present, otherwise offer the recommended stable "
            "user-data directory. Do not use the plugin directory."
        ),
    }


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


def assessment_signature(entry: dict[str, Any]) -> tuple[Any, Any, Any]:
    return entry.get("recorded_at"), entry.get("stage"), entry.get("score")


def read_assessment_history(learning_dir: Path) -> list[dict[str, Any]]:
    path = learning_dir / HISTORY_FILENAME
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            entries.append(item)
    return entries


def write_assessment_history(learning_dir: Path, entries: list[dict[str, Any]]) -> None:
    path = learning_dir / HISTORY_FILENAME
    with path.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def append_assessment_history(learning_dir: Path, entry: dict[str, Any]) -> None:
    path = learning_dir / HISTORY_FILENAME
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def migrate_legacy_mastery(learning_dir: Path, state: dict[str, Any]) -> bool:
    legacy = state.pop("mastery", None)
    if not isinstance(legacy, list) or not legacy:
        return legacy is not None
    history = read_assessment_history(learning_dir)
    known = {assessment_signature(item) for item in history}
    for entry in legacy:
        if isinstance(entry, dict) and assessment_signature(entry) not in known:
            history.append(entry)
            known.add(assessment_signature(entry))
    write_assessment_history(learning_dir, history)
    return True


def read_roadmap(learning_dir: Path) -> dict[str, Any] | None:
    path = learning_dir / ROADMAP_FILENAME
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("modules"), list):
        return None
    return payload


def flattened_concepts(roadmap: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not roadmap:
        return []
    concepts: list[dict[str, Any]] = []
    for module in roadmap.get("modules", []):
        if not isinstance(module, dict):
            continue
        module_id = str(module.get("id") or "module")
        module_weight = float(module.get("weight") or 1)
        module_concepts = module.get("concepts") or []
        concept_weight = module_weight / max(len(module_concepts), 1)
        for concept in module_concepts:
            if isinstance(concept, str):
                concept = {"id": normalize_text(concept), "title": concept}
            if not isinstance(concept, dict):
                continue
            concepts.append(
                {
                    **concept,
                    "id": str(concept.get("id") or normalize_text(str(concept.get("title", "concept")))),
                    "title": str(concept.get("title") or concept.get("id") or "concept"),
                    "module_id": module_id,
                    "module_title": str(module.get("title") or module_id),
                    "weight": float(concept.get("weight") or concept_weight),
                }
            )
    return concepts


def entry_matches_concept(entry: dict[str, Any], concept: dict[str, Any]) -> bool:
    explicit = entry.get("concepts") or []
    concept_id = normalize_text(str(concept.get("id", "")))
    concept_title = normalize_text(str(concept.get("title", "")))
    for value in explicit:
        normalized = normalize_text(str(value))
        if normalized and normalized in {concept_id, concept_title}:
            return True
    stage = str(entry.get("stage") or "").lower()
    return any(str(pattern).lower() in stage for pattern in concept.get("stage_patterns", []))


def weighted_recent_score(entries: list[dict[str, Any]]) -> float:
    recent = entries[-5:]
    if not recent:
        return 0.0
    weights = list(range(1, len(recent) + 1))
    return round(
        sum(float(item.get("score") or 0) * weight for item, weight in zip(recent, weights))
        / sum(weights),
        1,
    )


def assessment_statistics(history: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [float(item.get("score") or 0) for item in history]
    recent = scores[-5:]
    previous = scores[-10:-5]
    recent_average = round(statistics.mean(recent), 1) if recent else 0.0
    previous_average = round(statistics.mean(previous), 1) if previous else recent_average
    return {
        "assessment_count": len(scores),
        "average_score": round(statistics.mean(scores), 1) if scores else 0.0,
        "recent_average": recent_average,
        "trend": round(recent_average - previous_average, 1),
        "active_days": len({str(item.get("recorded_at", ""))[:10] for item in history if item.get("recorded_at")}),
        "applied_evidence_count": sum(
            1 for item in history if item.get("evidence") in {"apply", "code", "build"}
        ),
    }


def build_progress_snapshot(
    learning_dir: Path, state: dict[str, Any], history: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    history = history if history is not None else read_assessment_history(learning_dir)
    roadmap = read_roadmap(learning_dir)
    concepts = flattened_concepts(roadmap)
    stats = assessment_statistics(history)
    concept_rows: list[dict[str, Any]] = []
    for concept in concepts:
        evidence = [entry for entry in history if entry_matches_concept(entry, concept)]
        score = weighted_recent_score(evidence)
        evidence_types = {str(entry.get("evidence") or "recall") for entry in evidence}
        evidence_factor = max(
            ({"recall": 0.65, "explain": 0.8, "apply": 1.0, "code": 1.0, "build": 1.0}.get(kind, 0.65)
             for kind in evidence_types),
            default=0.0,
        )
        if len(evidence) >= 3 and score >= 8.5 and evidence_types & {"apply", "code", "build"}:
            status = "mastered"
        elif len(evidence) >= 2 and score >= 8:
            status = "solid"
        elif evidence:
            status = "developing"
        else:
            status = "not_started"
        concept_rows.append(
            {
                "id": concept["id"],
                "title": concept["title"],
                "module_id": concept["module_id"],
                "module_title": concept["module_title"],
                "weight": concept["weight"],
                "score": score,
                "verified_score": round(score * evidence_factor, 1),
                "evidence_count": len(evidence),
                "status": status,
            }
        )

    total_weight = sum(row["weight"] for row in concept_rows) or 1.0
    covered_weight = sum(row["weight"] for row in concept_rows if row["evidence_count"])
    mastery_weight = sum(row["weight"] * row["score"] / 10 for row in concept_rows)
    verified_weight = sum(row["weight"] * row["verified_score"] / 10 for row in concept_rows)
    coverage = round(covered_weight / total_weight * 100) if concept_rows else None
    curriculum_mastery = round(mastery_weight / total_weight * 100) if concept_rows else None
    verified_mastery = round(verified_weight / total_weight * 100) if concept_rows else None
    learned_scores = [row["score"] for row in concept_rows if row["evidence_count"]]
    learned_mastery = (
        round(statistics.mean(learned_scores) * 10)
        if learned_scores
        else round(stats["average_score"] * 10)
    )

    modules: list[dict[str, Any]] = []
    if roadmap:
        for module in roadmap.get("modules", []):
            rows = [row for row in concept_rows if row["module_id"] == str(module.get("id") or "module")]
            modules.append(
                {
                    "title": str(module.get("title") or module.get("id") or "module"),
                    "coverage_percent": round(
                        sum(1 for row in rows if row["evidence_count"]) / max(len(rows), 1) * 100
                    ),
                    "mastery_percent": round(
                        statistics.mean(row["score"] for row in rows) * 10
                    ) if rows else 0,
                }
            )

    if coverage is None:
        ability_level = "尚未建立课程地图"
    elif coverage < 25:
        ability_level = "入门起步"
    elif coverage < 50:
        ability_level = "基础心智模型建立中"
    elif not stats["applied_evidence_count"]:
        ability_level = "基础心智模型已建立，待代码应用"
    elif coverage < 75:
        ability_level = "常见场景实践中"
    elif curriculum_mastery is not None and curriculum_mastery < 75:
        ability_level = "综合巩固中"
    else:
        ability_level = "可独立应用"

    strengths = [
        row["title"]
        for row in sorted(concept_rows, key=lambda item: (item["score"], item["evidence_count"]), reverse=True)
        if row["status"] in {"solid", "mastered"}
    ][:5]
    focus = [
        row["title"]
        for row in sorted(
            concept_rows,
            key=lambda item: (item["evidence_count"] == 0, item["score"] if item["evidence_count"] else 99),
        )
        if row["status"] == "developing"
    ][:5]
    latest = history[-1] if history else state.get("latest_assessment")
    return {
        "topic": state.get("topic"),
        "current_step": state.get("current_step"),
        "next_task": state.get("next_step"),
        "ability_level": ability_level,
        "course_coverage_percent": coverage,
        "curriculum_mastery_percent": curriculum_mastery,
        "verified_mastery_percent": verified_mastery,
        "learned_material_mastery_percent": learned_mastery,
        **stats,
        "mastered_concepts": sum(1 for row in concept_rows if row["status"] == "mastered"),
        "solid_concepts": sum(1 for row in concept_rows if row["status"] == "solid"),
        "total_concepts": len(concept_rows),
        "strengths": strengths,
        "focus_concepts": focus,
        "modules": modules,
        "latest_assessment": latest,
    }


def update_assessment_log(learning_dir: Path, history: list[dict[str, Any]]) -> None:
    lines = ["# Assessment", "", "## Recent Evidence", ""]
    for entry in history[-RECENT_ASSESSMENT_LIMIT:]:
        lines.extend(
            [
                f"### {entry.get('recorded_at', '')[:10]} {entry.get('stage', '')}",
                "",
                f"- Score: {entry.get('score')}/10",
                f"- Evidence: {entry.get('evidence', 'recall')}",
                f"- Concepts: {', '.join(str(x) for x in entry.get('concepts', [])) or 'Not tagged'}",
                f"- Correction: {entry.get('feedback') or '; '.join(str(x) for x in entry.get('weak_concepts', [])) or 'None'}",
                f"- Next task: {entry.get('next_task', '')}",
                "",
            ]
        )
    lines.extend(
        [
            "## History",
            "",
            f"Full machine-readable history: `{HISTORY_FILENAME}`.",
            "",
        ]
    )
    (learning_dir / "assessment.md").write_text("\n".join(lines), encoding="utf-8")


def update_progress_index(learning_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    snapshot = build_progress_snapshot(learning_dir, state)
    latest = snapshot.get("latest_assessment") or {}
    weak = latest.get("weak_concepts") or []
    weak_text = "; ".join(str(item) for item in weak) or "None recorded"
    progress_value = snapshot.get("course_coverage_percent")
    progress_text = f"{progress_value}%" if progress_value is not None else "unknown"
    mastery_value = snapshot.get("learned_material_mastery_percent")
    verified_value = snapshot.get("verified_mastery_percent")
    verified_text = f"{verified_value}%" if verified_value is not None else "unknown"
    modules = "\n".join(
        f"- {item['title']}: coverage {item['coverage_percent']}%, mastery {item['mastery_percent']}%"
        for item in snapshot.get("modules", [])
    ) or "- No roadmap configured yet."
    content = (
        "# Progress Index\n\n"
        "## Dashboard\n\n"
        f"- Topic: {snapshot.get('topic')}\n"
        f"- Level: {snapshot.get('ability_level')}\n"
        f"- Course coverage: {progress_text}\n"
        f"- Mastery of learned material: {mastery_value}%\n"
        f"- Verified curriculum mastery: {verified_text}\n"
        f"- Assessments: {snapshot.get('assessment_count')} across {snapshot.get('active_days')} active days\n"
        f"- Recent average: {snapshot.get('recent_average')}/10 (trend {snapshot.get('trend'):+.1f})\n"
        f"- Current step: {snapshot.get('current_step')}\n"
        f"- Next task: {snapshot.get('next_task')}\n"
        f"- Updated at: {state.get('updated_at')}\n\n"
        "## Modules\n\n"
        f"{modules}\n\n"
        "## Strengths And Focus\n\n"
        f"- Strengths: {', '.join(snapshot.get('strengths', [])) or 'Not enough tagged evidence'}\n"
        f"- Focus: {', '.join(snapshot.get('focus_concepts', [])) or weak_text}\n\n"
        "## Latest Assessment\n\n"
        f"- Stage: {latest.get('stage')}\n"
        f"- Score: {latest.get('score')}\n"
        f"- Weak concepts: {weak_text}\n\n"
        "## Fast Resume Protocol\n\n"
        "1. Run `status` and use its compact snapshot first.\n"
        "2. Read only the current lesson or a specifically needed reference.\n"
        "3. Do not read the full assessment history during ordinary tutoring turns.\n"
        "4. Show a one-line progress update every three scored checks and at session end.\n"
    )
    (learning_dir / "progress-index.md").write_text(content, encoding="utf-8")
    return snapshot


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
    configured = configured_learning_root()
    if not args.root and configured is None:
        return storage_confirmation_payload()
    if (
        not args.root
        and load_config().get("confirm_new_topic_root", True)
        and not args.confirmed_root
    ):
        return storage_confirmation_payload(configured)
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
    migrate_legacy_mastery(learning_dir, state)
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
            "latest_assessment": state.get("latest_assessment"),
            "assessment_summary": state.get("assessment_summary", {}),
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
    snapshot = build_progress_snapshot(learning_dir, state)
    state["assessment_summary"] = {
        key: snapshot[key]
        for key in ("assessment_count", "average_score", "recent_average", "trend", "active_days", "applied_evidence_count")
    }
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
    if not args.root and configured_learning_root() is None:
        return storage_confirmation_payload()
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
    if not 0 <= args.score <= 10:
        raise SystemExit("--score must be between 0 and 10")
    learning_root = resolve_learning_root(args.root)
    learning_dir = (learning_root / args.slug).resolve()
    state = read_state(learning_dir)
    if not state:
        raise SystemExit(f"No learning_state.json found for slug: {args.slug}")

    migrate_legacy_mastery(learning_dir, state)

    entry = {
        "recorded_at": now_iso(),
        "stage": args.stage,
        "score": args.score,
        "concepts": args.concept or [],
        "evidence": args.evidence,
        "weak_concepts": args.weak_concepts or [],
        "next_task": args.next_task,
    }
    if args.learner_answer:
        entry["learner_answer"] = args.learner_answer
    if args.canonical_answer:
        entry["canonical_answer"] = args.canonical_answer
    if args.feedback:
        entry["feedback"] = args.feedback
    append_assessment_history(learning_dir, entry)
    state["updated_at"] = now_iso()
    state["next_step"] = args.next_task
    state["current_step"] = args.stage
    state["latest_assessment"] = entry
    state.pop("_state_path", None)
    state.pop("_learning_dir", None)
    history = read_assessment_history(learning_dir)
    snapshot = build_progress_snapshot(learning_dir, state, history)
    state["assessment_summary"] = {
        key: snapshot[key]
        for key in ("assessment_count", "average_score", "recent_average", "trend", "active_days", "applied_evidence_count")
    }
    write_json(learning_dir / "learning_state.json", state)
    update_assessment_log(learning_dir, history)
    update_progress_index(learning_dir, state)
    return {
        "status": "assessment_recorded",
        "learning_dir": str(learning_dir),
        "resume_snapshot": build_progress_snapshot(learning_dir, state, history),
    }


def set_roadmap(args: argparse.Namespace) -> dict[str, Any]:
    learning_root = resolve_learning_root(args.root)
    learning_dir = (learning_root / args.slug).resolve()
    state = read_state(learning_dir)
    if not state:
        raise SystemExit(f"No learning_state.json found for slug: {args.slug}")
    source = Path(args.file).expanduser().resolve()
    try:
        roadmap = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid roadmap JSON: {exc}") from exc
    concepts = flattened_concepts(roadmap)
    if not roadmap.get("modules") or not concepts:
        raise SystemExit("Roadmap must contain at least one module and one concept")
    write_json(learning_dir / ROADMAP_FILENAME, roadmap)
    migrate_legacy_mastery(learning_dir, state)
    state["updated_at"] = now_iso()
    state["roadmap_summary"] = {
        "goal": roadmap.get("goal"),
        "module_count": len(roadmap.get("modules", [])),
        "concept_count": len(concepts),
    }
    state.pop("_state_path", None)
    state.pop("_learning_dir", None)
    write_json(learning_dir / "learning_state.json", state)
    snapshot = update_progress_index(learning_dir, state)
    return {"status": "roadmap_saved", "learning_dir": str(learning_dir), "resume_snapshot": snapshot}


def show_status(args: argparse.Namespace) -> dict[str, Any]:
    learning_root = resolve_learning_root(args.root)
    learning_dir = (learning_root / args.slug).resolve()
    state = read_state(learning_dir)
    if not state:
        raise SystemExit(f"No learning_state.json found for slug: {args.slug}")
    changed = migrate_legacy_mastery(learning_dir, state)
    state.pop("_state_path", None)
    state.pop("_learning_dir", None)
    snapshot = build_progress_snapshot(learning_dir, state)
    state["latest_assessment"] = snapshot.get("latest_assessment")
    state["assessment_summary"] = {
        key: snapshot[key]
        for key in ("assessment_count", "average_score", "recent_average", "trend", "active_days", "applied_evidence_count")
    }
    if changed:
        state["updated_at"] = now_iso()
    write_json(learning_dir / "learning_state.json", state)
    update_progress_index(learning_dir, state)
    return {"status": "ok", "learning_dir": str(learning_dir), "resume_snapshot": snapshot}


def compact_learning(args: argparse.Namespace) -> dict[str, Any]:
    learning_root = resolve_learning_root(args.root)
    learning_dir = (learning_root / args.slug).resolve()
    state = read_state(learning_dir)
    if not state:
        raise SystemExit(f"No learning_state.json found for slug: {args.slug}")
    migrate_legacy_mastery(learning_dir, state)
    assessment_path = learning_dir / "assessment.md"
    archive_path = learning_dir / "assessment-archive.md"
    if assessment_path.exists() and not archive_path.exists():
        archive_path.write_text(assessment_path.read_text(encoding="utf-8"), encoding="utf-8")
    history = read_assessment_history(learning_dir)
    update_assessment_log(learning_dir, history)
    state.pop("_state_path", None)
    state.pop("_learning_dir", None)
    state["updated_at"] = now_iso()
    snapshot = build_progress_snapshot(learning_dir, state, history)
    state["latest_assessment"] = snapshot.get("latest_assessment")
    state["assessment_summary"] = {
        key: snapshot[key]
        for key in ("assessment_count", "average_score", "recent_average", "trend", "active_days", "applied_evidence_count")
    }
    write_json(learning_dir / "learning_state.json", state)
    update_progress_index(learning_dir, state)
    return {
        "status": "compacted",
        "learning_dir": str(learning_dir),
        "archive": str(archive_path) if archive_path.exists() else None,
        "resume_snapshot": snapshot,
    }


def record_checkpoint(args: argparse.Namespace) -> dict[str, Any]:
    learning_root = resolve_learning_root(args.root)
    learning_dir = (learning_root / args.slug).resolve()
    state = read_state(learning_dir)
    if not state:
        raise SystemExit(f"No learning_state.json found for slug: {args.slug}")
    migrate_legacy_mastery(learning_dir, state)
    state["current_step"] = args.step
    state["next_step"] = args.next_task
    state["updated_at"] = now_iso()
    if args.note:
        state["checkpoint_note"] = args.note
    state.pop("_state_path", None)
    state.pop("_learning_dir", None)
    write_json(learning_dir / "learning_state.json", state)
    snapshot = update_progress_index(learning_dir, state)
    return {
        "status": "checkpoint_recorded",
        "learning_dir": str(learning_dir),
        "resume_snapshot": snapshot,
    }


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
    history = read_assessment_history(learning_dir)
    known = {assessment_signature(item) for item in history}
    for entry in state.get("mastery", []):
        if isinstance(entry, dict) and assessment_signature(entry) not in known:
            history.append(entry)
    return {
        "status": status,
        "learning_dir": str(learning_dir),
        "state_path": str(learning_dir / "learning_state.json"),
        "resume_snapshot": build_progress_snapshot(learning_dir, state, history),
        "progress_index": str(learning_dir / "progress-index.md"),
    }


def migrate_topic(args: argparse.Namespace) -> dict[str, Any]:
    source_root = validate_learning_root(Path(os.path.expanduser(args.source_root)))
    target_root = validate_learning_root(Path(os.path.expanduser(args.target_root)))
    source_dir = (source_root / args.slug).resolve()
    target_dir = (target_root / args.slug).resolve()
    state = read_state(source_dir)
    if not state:
        raise SystemExit(f"No learning_state.json found for slug: {args.slug}")
    if target_dir.exists() and any(target_dir.iterdir()):
        raise SystemExit(f"Target topic directory is not empty: {target_dir}")

    target_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
    migrated_state = read_state(target_dir)
    if not migrated_state:
        raise SystemExit(f"Migration did not produce a valid state file: {target_dir}")
    migrated_state["learning_root"] = str(target_root)
    migrated_state["learning_dir"] = str(target_dir)
    migrated_state["migrated_from"] = str(source_dir)
    migrated_state["updated_at"] = now_iso()
    migrated_state.pop("_state_path", None)
    migrated_state.pop("_learning_dir", None)
    write_json(target_dir / "learning_state.json", migrated_state)

    if args.set_default:
        config = load_config()
        config["default_learning_root"] = str(target_root)
        write_config(config)

    return {
        "status": "topic_migrated",
        "source_preserved": str(source_dir),
        "learning_dir": str(target_dir),
        "default_learning_root": (
            str(target_root) if args.set_default else load_config().get("default_learning_root")
        ),
        "resume_snapshot": build_progress_snapshot(target_dir, migrated_state),
    }


def show_config(args: argparse.Namespace) -> dict[str, Any]:
    if args.init:
        ensure_config()
    selected: Path | None = None
    if args.set_learning_root:
        selected = validate_learning_root(
            Path(os.path.expanduser(args.set_learning_root))
        )
    elif args.use_recommended_root:
        selected = validate_learning_root(recommended_learning_root())
    if selected:
        selected.mkdir(parents=True, exist_ok=True)
        config = load_config()
        config["default_learning_root"] = str(selected)
        write_config(config)
    config = load_config()
    configured = configured_learning_root()
    return {
        "status": "configured" if configured else "needs_storage_confirmation",
        "config_path": str(CONFIG_PATH),
        "recommended_learning_root": str(recommended_learning_root()),
        "configured_learning_root": str(configured) if configured else None,
        "configured_root_exists": configured.exists() if configured else False,
        "config": config,
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
    init_cmd.add_argument("--confirmed-root", action="store_true")
    init_cmd.set_defaults(func=init_learning)

    cont = sub.add_parser("continue", help="Find a learning folder to resume")
    cont.add_argument("--query")
    cont.add_argument("--root")
    cont.set_defaults(func=continue_learning)

    assess = sub.add_parser("assess", help="Record a mastery assessment summary")
    assess.add_argument("--slug", required=True)
    assess.add_argument("--stage", required=True)
    assess.add_argument("--score", type=float, required=True)
    assess.add_argument("--concept", action="append")
    assess.add_argument(
        "--evidence",
        choices=["recall", "explain", "apply", "code", "build"],
        default="recall",
    )
    assess.add_argument("--weak-concepts", action="append")
    assess.add_argument("--learner-answer")
    assess.add_argument("--canonical-answer")
    assess.add_argument("--feedback")
    assess.add_argument("--next-task", required=True)
    assess.add_argument("--root")
    assess.set_defaults(func=record_assessment)

    plan = sub.add_parser("plan", help="Attach a structured roadmap to a learning topic")
    plan.add_argument("--slug", required=True)
    plan.add_argument("--file", required=True)
    plan.add_argument("--root")
    plan.set_defaults(func=set_roadmap)

    status = sub.add_parser("status", help="Return a compact progress and mastery snapshot")
    status.add_argument("--slug", required=True)
    status.add_argument("--root")
    status.set_defaults(func=show_status)

    compact = sub.add_parser("compact", help="Migrate verbose state into compact indexed history")
    compact.add_argument("--slug", required=True)
    compact.add_argument("--root")
    compact.set_defaults(func=compact_learning)

    checkpoint = sub.add_parser(
        "checkpoint", help="Advance the learning pointer without creating an assessment"
    )
    checkpoint.add_argument("--slug", required=True)
    checkpoint.add_argument("--step", required=True)
    checkpoint.add_argument("--next-task", required=True)
    checkpoint.add_argument("--note")
    checkpoint.add_argument("--root")
    checkpoint.set_defaults(func=record_checkpoint)

    migrate = sub.add_parser(
        "migrate-topic", help="Copy a topic to another learning root without deleting the source"
    )
    migrate.add_argument("--slug", required=True)
    migrate.add_argument("--source-root", required=True)
    migrate.add_argument("--target-root", required=True)
    migrate.add_argument("--set-default", action="store_true")
    migrate.set_defaults(func=migrate_topic)

    config = sub.add_parser("config", help="Show or initialize configuration")
    config.add_argument("--init", action="store_true")
    config_root = config.add_mutually_exclusive_group()
    config_root.add_argument("--set-learning-root")
    config_root.add_argument("--use-recommended-root", action="store_true")
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
