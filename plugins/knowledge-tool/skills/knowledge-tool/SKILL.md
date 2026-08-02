---
name: knowledge-tool
description: Guide Codex to use KnowledgeTool when the user invokes @KnowledgeTool, asks to quickly learn any topic, learn a code project, create a structured learning plan, generate resumable learning documents, continue a prior learning topic such as "继续Android Compose", run mastery checks, retrieval practice, Feynman review, or create a one-page cheat sheet. Use for interview-driven learning workflows that save progress outside the plugin directory.
---

# KnowledgeTool

Use this skill when the user asks with `@KnowledgeTool ...` or wants a structured, resumable way to learn a topic or code project.

## Core Rule

Keep plugin source and user learning content separate. Never write learning notes, progress, generated questions, project maps, or user answers inside the plugin directory. Use `scripts/knowledge_tool.py` to create or locate the external learning directory before generating user content.

## Command Patterns

- `@KnowledgeTool <topic>`: create or resume a topic learning folder.
- `@KnowledgeTool 学习项目 <path>`: create or resume a code-project learning folder and scan the project read-only.
- `@KnowledgeTool 继续`: resume the most recently updated learning folder.
- `@KnowledgeTool 继续<topic>` or `@KnowledgeTool 继续 <topic>`: resume a matching topic, for example `@KnowledgeTool 继续Android Compose`.
- `保存到 <path>`: override the learning root for that request.

## Setup And State

1. Resolve the learning root:
   - If the user says `保存到 <path>`, pass that path to the script with `--root`.
   - Otherwise let the script read `~/.knowledge-tool/config.json`.
   - If no config exists, the script defaults to `<current workspace>/.knowledge-tool/learning`.
2. For a new topic, run:
   `python <plugin>/scripts/knowledge_tool.py init --topic "<topic>"`
3. For a code project, run:
   `python <plugin>/scripts/knowledge_tool.py init --topic "<project name or topic>" --mode project --project-path "<path>"`
4. For continuation, run:
   `python <plugin>/scripts/knowledge_tool.py continue --query "<topic>"` or omit `--query` for latest.
5. Read the returned JSON. Use `learning_dir` and `files` from the script as the only destinations for generated learning content.
6. For continuation, read `learning_state.json` and `progress-index.md` first. Read longer files only when the current step or learner's question requires them.

If `continue` returns multiple candidates, show the candidates and ask the user which one to continue.

## Fast Resume And Context Budget

KnowledgeTool should optimize for fast tutoring turns, not exhaustive context loading:

- Default to concise, direct answers in the user's language, followed by at most one focused retrieval question.
- Use `progress-index.md` as the first human-readable index for where the learner is, recent scores, weak concepts, and the next task.
- Keep `context-summary.md` as a compact learner model and concept summary when a session becomes long.
- After each assessment, stage change, or meaningful correction, update `assessment.md` and use `scripts/knowledge_tool.py assess` so `learning_state.json` and `progress-index.md` stay current.
- Avoid rereading all learning documents on every turn. Prefer the current-stage file and the index.
- The plugin cannot force Codex to switch model or speed modes by itself. If the host exposes a model or speed control, follow the user's fast-mode preference. Otherwise, emulate fast mode through shorter answers, smaller context reads, and one-question-at-a-time teaching.

## Learning Workflow

Read `references/learning-flow.md` before generating or continuing the study content. Follow the stages in order unless the saved state says the learner is repeating a remediation loop.

Each stage must update the appropriate Markdown file and end with a concrete next step:

1. Learner interview
2. Five-perspective STORM exploration
3. Conflict map
4. Integrated research brief
5. Peer-review self-check
6. Resource triage
7. Learning ladder
8. Core 20 percent lesson plan
9. Mastery assessment and retrieval practice
10. Feynman loop
11. One-page cheat sheet

## Mastery Checks

Include assessment throughout the flow, even if the user did not ask for tests. Keep it constructive and adaptive:

- Before planning: 3 diagnostic questions to estimate current level.
- After each learning level: 3 multiple-choice questions, 2 short-answer questions, and 1 hands-on task.
- When resuming: a 3-5 minute recovery quiz before deciding whether to continue, review, or enter Feynman remediation.
- During active testing: ask one question at a time, wait for the learner's answer, score 0-10, identify gaps, and update `assessment.md`.
- After every learner answer, provide the canonical answer before or alongside feedback. Do not only comment on the learner's response. The feedback shape should be: score, canonical answer, what the learner got right, precise corrections, and one next question or task.
- Prefer free-recall questions over recognition questions. Do not provide an answer bank, option list, or multiple-choice choices unless the learner asks for them, the learner is a beginner who needs scaffolding, or the task specifically requires multiple-choice practice. For classification drills, give only the scenarios and ask the learner to name the mechanism and justify it.
- Avoid answer-order leakage. Do not make answers follow the same order as options, examples, state buckets, or concepts introduced immediately before the question. Randomize or deliberately vary option order, scenario order, and answer mappings. For matching/classification questions, include at least one reordered scenario or distractor, and do not ask questions where the correct response is simply "the same order as above".
- Avoid count-matching leakage. Do not habitually make the number of scenarios equal the number of answer choices, because that encourages one-to-one guessing. Prefer uneven counts, reused answers, plausible distractors, or an explicit "none/depends" option when appropriate.
- When asking multi-part questions, prefer scenario labels such as A/B/C/D or realistic named cases over lists whose answer is obvious from position. Record the canonical answer in `assessment.md` only after the learner responds.
- Make questions precise about lifecycle and duration. For effect APIs such as `LaunchedEffect`, distinguish "starts once", "keeps collecting while in composition", "restarts when key changes", and "is cancelled when leaving composition". Do not phrase a sustained listener as if it only listens once.
- Make scenario questions explicit about assumptions that change the answer. For event-flow questions, state whether the screen is still alive, whether the event may be dropped, whether delayed delivery is desired, whether multiple collectors exist, and whether the event should be consumed once or broadcast. Avoid vague prompts such as "the page is not in composition" without saying whether the expected UX is to drop, buffer, or persist the event.

Use `scripts/knowledge_tool.py assess` after scoring to record the score, weak concepts, and next task in `learning_state.json`.

## Code Project Mode

For project learning:

- Inspect the target project read-only.
- Prefer existing README, dependency manifests, entrypoints, architecture files, and tests.
- Generate `project-map.md`, `architecture-notes.md`, and `hands-on-tasks.md`.
- Convert the project structure into a learning ladder and hands-on tasks.
- Do not modify the project being learned unless the user separately asks for code changes.

## Output Style

Write learning documents in the user's language by default. For this plugin, Chinese is the default unless the user asks otherwise or config sets another language.

Keep each generated document useful on its own, with concise headings, explicit next actions, and references to the current stage. Avoid dumping long generic explanations; make the learner do retrieval, explanation, and small projects.
