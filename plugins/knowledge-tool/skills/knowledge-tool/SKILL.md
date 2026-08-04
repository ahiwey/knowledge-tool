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
- `@KnowledgeTool 进度` or `@KnowledgeTool <topic>进度`: show the compact dashboard before teaching.
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
5. Read the returned JSON. Use `learning_dir` as the only destination for generated learning content.
6. For continuation or progress questions, run `status --slug <slug>` and use only `resume_snapshot` first. Read `progress-index.md` only when the learner asks for detail. Do not read `assessment-history.jsonl` during ordinary tutoring.
7. After the interview, create a topic roadmap JSON with modules, weighted concepts, and `stage_patterns`, then attach it with `plan --slug <slug> --file <roadmap.json>`. Without a roadmap, report mastery of completed checks but label total course progress as unknown.

If `continue` returns multiple candidates, show the candidates and ask the user which one to continue.

## Fast Resume And Context Budget

KnowledgeTool should optimize for learning per minute, not number of tutoring turns:

- Default to a sprint turn: concise correction or lesson, smallest useful example, then one focused free-recall or code task.
- When the learner wants faster progress, use a micro-batch of two or three free-recall prompts answered in one message. Never add answer choices merely to batch questions.
- Run `status` to resume. Treat `assessment-history.jsonl` as cold history and `learning_state.json` as a compact pointer, not an event log.
- Use `scripts/knowledge_tool.py assess` with `--concept` and `--evidence` so the tool updates the rolling assessment log, knowledge-point mastery, and progress index deterministically. Do not manually append every answer to a growing Markdown file.
- Use `scripts/knowledge_tool.py checkpoint` after a lesson, example, or stage transition that has no learner score. Never leave the next-task pointer stale merely because no assessment occurred.
- Show a one-line dashboard every three scored checks and at session end: course coverage, mastery of learned material, recent trend, and next task.
- Keep `context-summary.md` only for stable learner preferences or unresolved conceptual models that cannot be represented by the roadmap and assessment data.
- The plugin cannot force Codex to switch model or speed modes by itself. If the host exposes a model or speed control, follow the user's fast-mode preference. Otherwise, emulate fast mode through shorter answers, smaller context reads, and one-question-at-a-time teaching.

## Learning Workflow

Read `references/learning-flow.md` before generating or continuing study content. Before asking mastery-check, retrieval-practice, or Feynman-loop questions, also read and apply `references/question-design.md`.

Choose the shortest workflow that matches the goal:

- Practical/code fast track: interview, diagnostic, roadmap, core lessons, code/application checks, spaced review, small project.
- Research/deep-understanding track: interview, STORM exploration, conflict map, brief, peer review, resource triage, ladder, assessment, Feynman review, cheat sheet.

Do not force STORM, conflict mapping, or a ten-lesson document onto a learner whose goal is practical skill. Every stage must end with a concrete next task and update the compact state when the task changes.

## Mastery Checks

Include assessment throughout the flow, even if the user did not ask for tests. Keep it constructive and adaptive:

- Before planning: use up to 3 diagnostic questions only when existing evidence is insufficient.
- After a lesson: prefer one application question. Use a two-to-three-question micro-batch when reducing round trips matters more than immediate adaptation.
- When resuming within seven days, continue from the compact snapshot without a mandatory recovery quiz. Use one retrieval prompt only when a concept is due for review or confidence is low.
- During active testing: normally ask one question at a time; use a two-to-three-question free-recall micro-batch when the learner prioritizes speed. Score 0-10, identify gaps, and run the helper's `assess` command.
- After every learner answer, provide the canonical answer before or alongside feedback. Do not only comment on the learner's response. The feedback shape should be: score, canonical answer, what the learner got right, precise corrections, and one next question or task.
- Prefer free-recall questions over recognition questions. Do not provide an answer bank, option list, or multiple-choice choices unless the learner asks for them, the learner is a beginner who needs scaffolding, or the task specifically requires multiple-choice practice. For classification drills, give only the scenarios and ask the learner to name the mechanism and justify it.
- Avoid answer-order leakage. Do not make answers follow the same order as options, examples, state buckets, or concepts introduced immediately before the question. Randomize or deliberately vary option order, scenario order, and answer mappings. For matching/classification questions, include at least one reordered scenario or distractor, and do not ask questions where the correct response is simply "the same order as above".
- Avoid count-matching leakage. Do not habitually make the number of scenarios equal the number of answer choices, because that encourages one-to-one guessing. Prefer uneven counts, reused answers, plausible distractors, or an explicit "none/depends" option when appropriate.
- When asking multi-part questions, prefer scenario labels such as A/B/C/D or realistic named cases over lists whose answer is obvious from position. Record the canonical answer in `assessment.md` only after the learner responds.
- Make questions precise about lifecycle and duration. For effect APIs such as `LaunchedEffect`, distinguish "starts once", "keeps collecting while in composition", "restarts when key changes", and "is cancelled when leaving composition". Do not phrase a sustained listener as if it only listens once.
- Make scenario questions explicit about assumptions that change the answer. For event-flow questions, state whether the screen is still alive, whether the event may be dropped, whether delayed delivery is desired, whether multiple collectors exist, and whether the event should be consumed once or broadcast. Avoid vague prompts such as "the page is not in composition" without saying whether the expected UX is to drop, buffer, or persist the event.
- Run a question quality gate before asking: one main concept, explicit assumptions, clear expected answer shape, learner-appropriate difficulty, and useful signal from likely wrong answers. Prefer plain-language situations before naming terms.
- If the learner says a question is unclear, inaccurate, too easy because of visible choices, or poorly scaled, treat that as assessment feedback. Record the teaching issue when useful, rewrite the question, and continue with the improved version.

Use `scripts/knowledge_tool.py assess` after scoring to append the full evidence history and regenerate compact state, the rolling assessment log, and the progress index.

Use these advancement rules to prevent slow remediation loops:

- Score 8-10: advance immediately and schedule later retrieval.
- Score 6-7.9: give one precise correction, record the gap, then advance unless it blocks the next concept.
- Score below 6: give one focused remediation turn. Do not spend more than two consecutive checks on the same boundary; defer it to spaced review if still weak.
- Treat `apply`, `code`, and `build` evidence as stronger than recognition. Do not call a concept mastered from one verbal answer.

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
