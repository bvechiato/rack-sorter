# Project instructions

## Living flow README (required)

`docs/flows/README.md` is the source of truth for current behavior: the system map, user flows, routes, state, external boundaries, and known gaps.

This applies to every task that changes runtime behavior (routes, state, integrations, or user journeys):

1. **Check current behavior first.** Read the relevant flow section and confirm it against the code and tests. If they disagree, the README is stale until proven otherwise.
2. **Update the README in the same task.** Change the affected flow section; update the system map if layers, edges, or shared state moved; update the fault map if a gap was added or fixed.
3. **Verify before finishing.** Re-check code vs README, run the repo checks, and update `Last verified`. If they disagree, the task is not done.

`Last verified` is a short scope statement of when and against what the README was checked. Do not append a list of changes made in the task; refresh only the date and commit when the verification target moves.

The flow README describes current design decisions and limits, not change history. Do not record issue numbers, past bugs, or how something was fixed; state what holds now so a developer can orient without reconstructing the change sequence.

Diagram rules: 8–14 nodes per flow, 12–18 for the system map. Short labels; detail goes in Gotchas. Never draw planned behavior as if it exists.

Do not invent E2E coverage. This repository has no browser E2E suite; use the manual checklist and coverage table in `docs/flows/README.md`.

Additional repo rules (no import-time side effects, local check commands) remain in `CONTRIBUTING.md`.
