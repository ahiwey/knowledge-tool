# Question Design Guide

Use this guide before asking retrieval-practice, mastery-check, or Feynman-loop questions.

The goal is not to make questions feel clever. The goal is to make the learner retrieve the exact concept needed for the next step.

## Question Quality Gate

Before asking a question, check these five points:

1. Target: The question tests one main concept, skill, or boundary.
2. Assumptions: The stem states any condition that changes the answer.
3. Answer shape: The learner knows what form of answer is expected, such as a short explanation, a classification with reasons, a code sketch, or a tradeoff.
4. Difficulty: The question matches the learner's current level and recent mistakes.
5. Signal: A wrong answer will reveal a useful misconception, not just a missing word.

If any point is weak, rewrite the question before asking it.

## Plain Language First

Use plain language before terminology:

- Better: "This message should happen once, then disappear. Should it be current screen state or a one-time event?"
- Worse: "Classify this as state or event."

Use technical terms after the learner has a concrete situation in mind.

## No Easy Option Banks By Default

Prefer free recall. Do not list answer choices unless the learner asks for choices, beginner scaffolding is needed, or the exercise specifically requires recognition practice.

For classification practice:

- Give realistic cases.
- Ask the learner to name the mechanism and justify it.
- Use uneven counts and repeated mechanisms when that improves learning.
- Do not make the number of scenarios match the number of possible answers by habit.

## One Boundary Per Question

Avoid mixing too many boundaries in one prompt. If the learner is practicing state ownership, do not also test event buffering and navigation unless the question explicitly says it is an integration exercise.

Good boundaries to isolate:

- Current UI state vs one-time UI event
- State owner vs event callback
- Route/container vs content/presentation
- Local UI state vs ViewModel state
- `remember`, `rememberSaveable`, ViewModel, Repository
- `StateFlow`, `SharedFlow`, Channel

## Compose Question Templates

### State vs Event

Ask:

```text
这个东西是“当前画面应该长什么样”的状态，还是“只发生一次的动作”？
如果页面重组、旋转、离开后回来，它应该再次出现吗？
```

### Route vs Content

Ask:

```text
哪一层拿 ViewModel 并收集 uiState？
哪一层只接收参数和回调？
用户点击后，事件从哪里传到哪里？
状态更新后，UI 又从哪里读到新值？
```

### Flow Event Delivery

Ask:

```text
这个事件可以在页面不收集时丢掉吗？
它需要等页面回来后只处理一次吗？
它要广播给多个收集者，还是只给一个消费者？
它被新收集者重复收到会不会出 bug？
```

## Feedback After Answers

After every learner answer, give:

1. Score.
2. Canonical answer.
3. What was right.
4. Precise correction.
5. One rewritten or follow-up question.

Do not only comment on the learner's answer. Always show the correct answer.

## When The Learner Flags A Bad Question

Treat question-quality feedback as high-priority learning data:

1. Briefly acknowledge the specific defect, such as vague assumptions, too many options, or answer-order hints.
2. Record it as a weak teaching pattern in the learning notes when relevant.
3. Improve the next question before continuing.
4. If the feedback applies to the plugin behavior, update the plugin rule rather than only apologizing.
