# KnowledgeTool Learning Flow

This workflow is based on a closed-loop AI learning method: path, test, compression, and feedback. The goal is not to collect more resources; it is to build usable understanding, expose blind spots, and preserve progress.

## Fast Context Protocol

Before expanding context, run the helper's `status` command and use `resume_snapshot`. It is the hot index. `assessment-history.jsonl` and archived Markdown are cold history and should not be loaded during ordinary tutoring. Use `context-summary.md` only for stable preferences or unresolved context that the structured state cannot represent.

Each teaching turn should usually provide:

- A direct answer or correction
- The smallest example that resolves the confusion
- One focused retrieval question
- A deterministic `assess` update when scoring or changing the next task

When teaching advances without a scored learner answer, run `checkpoint` with the new step and next task. Checkpoints move the pointer without inventing assessment evidence.

When the learner prioritizes speed, use two or three free-recall prompts in one micro-batch. This reduces repeated conversational overhead while preserving retrieval practice.

## Workflow Routing

Use the practical fast track for programming, tools, and work skills:

1. Learner interview and diagnostic
2. Weighted roadmap with observable milestones
3. Core 20 percent lessons
4. Application or code evidence
5. Spaced retrieval of weak concepts
6. Small project and cheat sheet

Use the research track below only when the goal requires competing viewpoints, source synthesis, or deep research. Do not make a practical learner complete STORM and conflict mapping before useful practice.

## Progress Model

Create `roadmap.json` after the diagnostic. Define weighted modules and concepts, plus stage patterns that map assessment evidence back to concepts.

Report three different numbers instead of one vague percentage:

- Course coverage: how much of the roadmap has any evidence.
- Mastery of learned material: how well the covered material is currently understood.
- Curriculum mastery: mastery across the full roadmap, including unstarted concepts as zero.
- Verified curriculum mastery: curriculum mastery discounted when evidence is only recall or explanation; application, code, and build evidence receive full weight.

A high score on a narrow topic is not high course completion. A large amount of exposure is not mastery. Keep these measures separate.

## 0. Learner Interview

Collect only the information that changes the plan:

- Topic or project to learn
- Current level and prior experience
- Target use case: explain, build, interview, work task, research, or decision
- Available time: today, this week, and preferred session length
- Desired depth: overview, practical use, professional fluency, or expert research
- Practice environment: whether the learner can run code, write notes, or build a small project

Save the result in `interview.md` and `learning_state.json`.

## 1. Five-Perspective STORM

Analyze the topic from five viewpoints:

- Practitioner: what daily users know that outsiders miss
- Scholar: what peer-reviewed or deeply researched evidence says
- Skeptic: strongest counterarguments and ignored evidence
- Economist: incentives, costs, winners, and losers
- Historian: similar precedents and how they ended

For each viewpoint, capture:

- Two-sentence position
- Strongest evidence
- One insight other viewpoints would likely miss

## 2. Conflict Map

Map where the viewpoints disagree:

- Direct conflicts and evidence on each side
- Strongest and weakest claims
- One question that would resolve the largest conflict
- Claims all viewpoints accept
- Blind spots no viewpoint mentioned

## 3. Integrated Research Brief

Compress the exploration into `research-brief.md`:

- One CEO-ready paragraph
- Five key findings ordered by reliability
- Which viewpoints support or oppose each finding
- One hidden relationship visible only after combining viewpoints
- One action recommendation for the learner's role
- One frontier question that could change the whole understanding

## 4. Peer-Review Self-Check

Critique the brief before using it:

- Score each finding 1-10 for reliability
- Identify the least certain conclusion and what evidence would verify it
- Identify viewpoint overweighting
- Decide whether a sixth viewpoint is needed
- List edits a strict professor or senior practitioner would request

## 5. Resource Triage

Select only five high-leverage resources:

- Why each resource is stronger than alternatives
- How to use it: read, watch, practice, or reference
- Estimated time
- One key takeaway to extract
- What resources are overhyped or should be avoided

Arrange the resources into a one-week route.

## 6. Learning Ladder

Create five levels:

1. Complete beginner
2. Basic understanding
3. Practical user
4. Problem solver
5. Confident practitioner

For each level, define:

- What the learner should understand
- What mastery looks like
- Key concepts or skills
- Milestone to advance
- Hands-on exercise or small project
- Common mistakes
- One self-test question

## 7. Core 20 Percent Plan

Find the 20 percent of concepts and skills that produce 80 percent of practical usefulness. Turn them into 10 lessons. Each lesson needs:

- Objective
- Key concepts
- Hands-on practice
- Recommended free or low-friction resource
- Expected result
- Five review questions

End with a final small project that proves practical use.

## 8. Mastery Assessment

Use retrieval practice. Do not give all answers at once.

Assessment design must pass a question quality gate before order-bias checks:

- Test one main concept, boundary, or skill per question unless explicitly running an integration drill.
- State the assumptions that change the answer.
- Make the expected answer shape clear: explanation, classification with reasons, code sketch, tradeoff, or correction.
- Match the difficulty to the learner's recent answers.
- Prefer questions where a wrong answer reveals a useful misconception.
- Use plain language first, then name the technical term.

Assessment design must avoid order bias:

- Prefer free recall first. For most retrieval checks, do not show an answer bank or choices; ask the learner to produce the concept, API, state holder, or mechanism from memory and briefly justify it.
- Do not place choices, scenarios, and expected answers in matching order.
- Shuffle or intentionally vary option order for multiple-choice, matching, and classification questions.
- Avoid making the number of scenarios equal the number of answer choices unless there is a strong pedagogical reason. Include extra choices, repeated choices, plausible distractors, or a "depends on assumptions" answer to prevent one-to-one guessing.
- Avoid questions where the learner can answer by echoing the previous list order rather than understanding the concept.
- For multi-part classification, use realistic scenario labels and mix the correct categories.
- Keep the canonical answer private until after the learner answers, then record the score and explanation.
- Phrase lifecycle questions precisely. If a construct starts a coroutine once but keeps collecting until the Composable leaves composition, say that explicitly in the question stem.
- For APIs with keys or lifecycle behavior, ask for both the trigger and duration, for example: "When does it start, when does it restart, and when is it cancelled?"
- For scenario questions, include the assumptions that determine the correct answer. In event-delivery questions, specify whether an event can be dropped, should wait for the UI to return, must be consumed by one collector, or should be broadcast to all active collectors.
- After the learner answers, always provide the canonical answer. Then score the learner's answer, explain what was correct, correct gaps, and ask only one focused follow-up.
- If the learner flags a question as vague, inaccurate, too dependent on visible choices, or poorly scaled, pause the quiz flow, record the teaching defect if useful, and rewrite the next question using the quality gate.

Question sequence:

- Questions 1-3: beginner
- Questions 4-6: intermediate
- Questions 7-8: advanced
- Questions 9-10: expert

After every learner answer:

- Score 0-10
- State the canonical answer clearly
- Say what is correct
- Identify precise gaps or errors
- Re-explain only the missing part
- Increase difficulty if strong; ask a follow-up if weak

Run the helper's `assess` command so it appends cold history and regenerates the rolling `assessment.md`, compact `learning_state.json`, and `progress-index.md`.

Record the concept id and evidence type with every scored answer:

- `recall`: names or states the idea from memory
- `explain`: explains boundaries and reasons
- `apply`: chooses and justifies an approach in a new scenario
- `code`: writes or corrects working code
- `build`: integrates the concept in a small project

Advance with this cadence:

- 8-10: move on and revisit later.
- 6-7.9: correct once and move on unless the gap blocks the next topic.
- Below 6: run one focused remediation turn; after two consecutive checks on the same boundary, defer it to spaced review instead of looping.

Do not require a recovery quiz on every resume. If the learner returns within seven days and the snapshot is clear, continue directly. Ask a recovery question only for due review, low-confidence state, or a long gap.

## 9. Feynman Loop

Use the loop for weak concepts:

1. Explain the concept simply with daily-life examples.
2. Ask the learner to explain it back in their own words.
3. Identify fuzzy words, skipped steps, and hidden assumptions.
4. Re-teach only those parts.
5. Repeat until the explanation is simple, accurate, and complete.

Do not let Feynman review become an endless gate. If one correction does not resolve the gap, record it for spaced review and continue with material that does not depend on it.

## 10. One-Page Cheat Sheet

Create `cheatsheet.md` for five-minute review:

- Plain-language definition
- Most important concepts, rules, formulas, or steps
- 3-5 realistic examples
- Common beginner mistakes and confusing points
- Before-use checklist
- Five rapid Q&A prompts

Use this before meetings, interviews, coding sessions, or teaching someone else.
