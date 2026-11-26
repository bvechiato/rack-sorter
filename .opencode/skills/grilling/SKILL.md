---
name: Grilling
description: Stress-test a plan, decision or idea by writing batched questions to a Markdown file the user can answer. Use when the user wants to be grilled, stress-test their thinking, or explore a design.
---

# Grilling (file-based)

Interview the user until you reach a shared understanding, but **do not ask questions in the chat**. Write each batch of questions into a Markdown file where the user can answer them at their own pace.

Map the subject as a **design tree**: every decision branches into the decisions that hang off it.

## Where the questions go

Default path: `docs/grilling/<topic-slug>.md`. Use a short kebab-case slug for the topic. If the repository already has a convention for decision notes or design docs, follow it instead.

One file per topic. Create directories as needed. If the file already exists, **append a new round** — never overwrite answers the user has written.

## Round format

Each round is a section in the file. Every question gets a title, enough context to decide, a recommended answer, and an empty slot for the user's answer.

````markdown
## Round <n> — <short round theme>

### Q<n> — <question title>

<Question body: context, options, tradeoffs. Multiple paragraphs are fine.>

**Recommended:** <your recommended answer, phrased so "yes" accepts it>

**Your answer:**

<!-- answer here -->

---

### Q<n+1> — <title>

...

---
````

Word each question so "yes" accepts the recommended answer. Number questions continuously across rounds (Q1, Q2, Q3, …) so they can be referenced unambiguously.

## Workflow

1. **Find facts yourself.** Anything answerable from the filesystem, code, docs or tools is your job, not a question for the user. Use sub-agents with fresh context for broader exploration. Do not block on it: an in-flight exploration is an unsettled prerequisite, so only questions downstream of it wait; write the rest of the frontier now.
2. **Build the design tree.** List the decisions and what each one depends on. Keep it in your working context; put a short "Decisions settled so far" summary at the top of the file and update it each round.
3. **Compute the frontier.** The frontier is every decision whose prerequisites are settled — the questions you can ask now without guessing at answers you have not heard. A question that depends on another still-open question belongs in a later round.
4. **Write the next round.** Append the whole frontier to the file in the format above. Include only decisions — never fact-finding requests.
5. **Stop.** Tell the user the file path and ask them to fill in the "Your answer" slots. Do not repeat the questions in chat, do not guess answers, and do not act on the plan yet.
6. **Resume on request.** When the user says they have answered (or asks you to continue), read the file, treat the filled-in slots as settled decisions, update the summary, recompute the frontier, and append the next round. Leave blank slots open: either repeat them in the next round or ask the user explicitly to answer before continuing.
7. **Finish.** When the frontier is empty, append a "Shared understanding" section summarising every settled decision, including what was deliberately left out. Then wait for the user's explicit confirmation. Only after that confirmation may you act.

## Rules

- Every round contains the full frontier, not one question at a time.
- Decisions belong to the user; recommendations belong to you. Never fill in the answer slot yourself.
- The file is the source of truth for answers. Re-read it before each round rather than relying on chat memory.
- Do not record facts, issue history or change narration in the file — only decisions and their rationale.
- Do not begin implementation, commits or external actions until the user confirms the shared understanding.
