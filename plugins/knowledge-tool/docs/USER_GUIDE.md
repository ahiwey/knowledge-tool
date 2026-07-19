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

During a test, KnowledgeTool asks one question at a time, scores your answer from 0-10, identifies weak concepts, and records the next task.

## Moving Or Backing Up Learning Files

Learning folders are plain Markdown and JSON. You can move them to another machine or directory. Update `~/.knowledge-tool/config.json` so `default_learning_root` points at the new location.
