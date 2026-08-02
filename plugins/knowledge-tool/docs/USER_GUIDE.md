# KnowledgeTool User Guide

KnowledgeTool helps you learn a topic or code project through an interview, a structured learning path, tests, Feynman review, and resumable notes.

## Common Commands

Start learning a topic:

```text
@KnowledgeTool Android Compose
```

Start learning a code project:

```text
@KnowledgeTool 学习项目 C:\Ai\Project\App
```

Continue the latest learning item:

```text
@KnowledgeTool 继续
```

Continue a specific topic:

```text
@KnowledgeTool 继续Android Compose
```

Specify where learning files should be saved:

```text
@KnowledgeTool Android Compose 保存到 D:\Learning
```

## What Gets Created

Each topic has its own directory:

```text
<learning_root>/<topic-slug>/
```

Typical files:

```text
learning_state.json
progress-index.md
context-summary.md
README.md
interview.md
research-brief.md
learning-path.md
assessment.md
feynman-log.md
cheatsheet.md
```

Code project mode also creates:

```text
project-map.md
architecture-notes.md
hands-on-tasks.md
```

## Learning Flow

KnowledgeTool guides you through:

1. Learner interview
2. Five-perspective research
3. Conflict map
4. Integrated brief and self-review
5. Resource triage
6. Learning ladder
7. Core 20 percent lesson plan
8. Retrieval-practice tests
9. Feynman review for weak concepts
10. One-page cheat sheet

## Mastery Checks

The plugin includes tests by default:

- Diagnostic questions before planning
- Multiple-choice and short-answer checks after each stage
- Hands-on tasks for practical topics
- A short recovery quiz whenever you continue later

During a test, KnowledgeTool asks one question at a time, scores your answer from 0-10, gives the canonical answer, identifies weak concepts, and records the next task.

KnowledgeTool should prefer free-recall questions. It should usually ask you to produce the answer from memory rather than giving an answer bank, unless you ask for choices or need beginner scaffolding.

KnowledgeTool should avoid answer-order clues. For multiple-choice, matching, and classification checks, it should shuffle or vary option order so you cannot pass by simply repeating the order of concepts introduced immediately before the question.

It should also avoid count-matching clues. For example, it should not regularly ask three scenarios with exactly three answer choices where each choice is used once. Good checks may reuse an answer, include extra choices, or include a "depends" option.

Questions should also be precise about lifecycle behavior. For example, when teaching `LaunchedEffect(Unit)`, KnowledgeTool should distinguish "starts once at this call site" from "keeps collecting while the Composable remains in composition".

Scenario questions should include the assumptions that change the answer. For example, event-delivery questions should say whether the event may be dropped, should be buffered until the UI returns, should be consumed by one collector, or should be broadcast to all active collectors.

## Speed And Context Use

KnowledgeTool is designed to resume from compact files first:

- `learning_state.json` stores the current step and next task.
- `progress-index.md` stores the latest score, weak concepts, and fast resume notes.
- `context-summary.md` stores a compact learner model for long sessions.

The plugin cannot force Codex to change the selected model or app speed mode by itself. It does, however, default to a fast tutoring style: short answers, minimal context loading, and one focused question at a time.

## Moving Or Backing Up Learning Files

Learning folders are plain Markdown and JSON. You can move them to another machine or directory. Update `~/.knowledge-tool/config.json` so `default_learning_root` points at the new location.
