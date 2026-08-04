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

Show current progress and mastery:

```text
@KnowledgeTool Android Compose进度
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
roadmap.json
assessment-history.jsonl
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

For programming and practical skills, KnowledgeTool uses a fast track:

1. Learner interview and diagnostic
2. Weighted roadmap
3. Core lessons
4. Application or code checks
5. Spaced review
6. Small project and cheat sheet

Research topics can still use the longer STORM, conflict-map, brief, and peer-review workflow.

## Mastery Checks

The plugin uses adaptive checks:

- Diagnostic questions before planning
- Free-recall and application checks after lessons
- Code or build evidence for practical topics
- Recovery questions only when review is due, confidence is low, or the learning gap is long

During a test, KnowledgeTool asks one question at a time, scores your answer from 0-10, gives the canonical answer, identifies weak concepts, and records the next task.

KnowledgeTool should prefer free-recall questions. It should usually ask you to produce the answer from memory rather than giving an answer bank, unless you ask for choices or need beginner scaffolding.

Before asking, KnowledgeTool should run a question quality check: one main concept, clear assumptions, clear answer shape, and difficulty matched to your recent answers. Questions should first describe a concrete situation in plain language, then use technical terms.

KnowledgeTool should avoid answer-order clues. For multiple-choice, matching, and classification checks, it should shuffle or vary option order so you cannot pass by simply repeating the order of concepts introduced immediately before the question.

It should also avoid count-matching clues. For example, it should not regularly ask three scenarios with exactly three answer choices where each choice is used once. Good checks may reuse an answer, include extra choices, or include a "depends" option.

Questions should also be precise about lifecycle behavior. For example, when teaching `LaunchedEffect(Unit)`, KnowledgeTool should distinguish "starts once at this call site" from "keeps collecting while the Composable remains in composition".

Scenario questions should include the assumptions that change the answer. For example, event-delivery questions should say whether the event may be dropped, should be buffered until the UI returns, should be consumed by one collector, or should be broadcast to all active collectors.

## Speed And Context Use

KnowledgeTool separates hot state from cold history:

- `learning_state.json` stores only the current pointer, latest assessment, and aggregate metrics.
- `assessment-history.jsonl` stores the full evidence history and is not loaded during normal turns.
- `progress-index.md` shows course coverage, mastery of learned material, recent trend, strengths, weak concepts, and the next task.
- `roadmap.json` defines the modules and concepts used to calculate progress.

The progress numbers mean different things:

- Course coverage: how much of the roadmap has been studied at least once.
- Mastery of learned material: how well the studied portion is understood.
- Curriculum mastery: mastery across the whole roadmap, including unstarted topics.
- Verified curriculum mastery: the full-roadmap score adjusted for evidence quality, so verbal recall does not count the same as code or project work.

For faster sessions, ask KnowledgeTool to use sprint mode. It can group two or three free-recall prompts into one message, while still avoiding visible answer choices. Scores of 8-10 advance immediately; scores of 6-7 receive one precise correction and are revisited later.

The plugin cannot force Codex to change the selected model or app speed mode by itself. It reduces latency and token use through compact status snapshots, rolling logs, short feedback, and fewer round trips.

## Moving Or Backing Up Learning Files

Learning folders are plain Markdown and JSON. You can move them to another machine or directory. Update `~/.knowledge-tool/config.json` so `default_learning_root` points at the new location.
