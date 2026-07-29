# Mini Architecture Decision Record

## Feature 1: Due Date + Overdue Filter

### Context

Tasks needed a due date so users could set and adjust deadlines (User Stories 1–2), have the API automatically recognize when a task is overdue (User Story 3: past due date and not `Done`), and let the frontend filter the task list down to only tasks that are not overdue (User Story 4).

### Decision

`due_date: Optional[date] = None` was added to `TaskCreate`, `TaskUpdate`, and `TaskResponse`, with a `field_validator` that parses the incoming value with the standard library's `date.fromisoformat` and rejects anything that isn't a valid `YYYY-MM-DD` date in the future. `is_overdue` on `TaskResponse` is never persisted directly — it is recomputed by `business_rules.is_task_overdue(due_date, status)` every time a task is read (`storage._with_computed_overdue`), so it reflects "today" at request time rather than whatever day the task was created or last updated. `GET /tasks` accepts an optional `not_overdue` query parameter that filters using this same recomputed value.

### Reason

Recomputing on read is the simplest way to keep `is_overdue` always correct without needing a background job, scheduler, or write-time update to "flip" tasks to overdue as the clock passes midnight. Parsing with the standard library `date` type avoided any new dependency, and the assignment's user stories only called for a strict, unambiguous `YYYY-MM-DD` format — not lenient/human-friendly date parsing.

### Alternatives Suggested by AI

While scoping the date-parsing approach, the AI flagged a fork in the road: "depending on how you want date parsing/validation handled (e.g. plain `datetime.date` via Pydantic vs. adding `python-dateutil` for flexible parsing), an entry may need to be added to your dependency file."

### Rejected Alternative

Adding `python-dateutil` for flexible date-string parsing (e.g. accepting "Jan 5 2027", "05/01/2027", etc.) was rejected. None of the four due-date user stories asked for flexible input formats — the acceptance criteria only distinguish "valid date" from "invalid date format" — so pulling in an extra dependency to parse formats nothing in the project would ever send was unnecessary scope creep for a learning project whose frontend always sends ISO dates.

### Consequences

**Advantage:** `is_overdue` can never drift out of sync with reality — there's no cache-invalidation or scheduled-job failure mode to reason about; every read is correct by construction.
**Limitation:** because `is_overdue` is computed rather than stored, there's no record of *when* a task actually became overdue, and the same recomputation cost is paid on every single read — acceptable at this project's scale (in-memory, single-process) but something a persisted/distributed store would need to revisit.

---

## Feature 2: Tags/Labels

### Context

Tasks needed to support one or more tags: adding tags on create/update with case-insensitive de-duplication (User Story 1), removing specific tags with a validation error if the tag doesn't exist (User Story 2), filtering the task list by an exact tag (User Story 3), and a separate case-insensitive tag search endpoint (User Story 4).

### Decision

`tags: list[str] = []` was added to all three task models with a shared validator (strip, reject blank, de-duplicate case-insensitively while preserving first-seen casing). Rather than treating `tags` on `TaskUpdate` as a full replacement list, two explicit fields were added — `add_tags` and `remove_tags` — so `PATCH` can express "add these" / "remove these" as discrete operations. `update_task` in `storage.py` special-cases these two fields: it validates removals against the task's current tags via `business_rules.validate_tag_removal` before applying anything, then merges additions, and only afterward folds the result back into the generic `model_copy` update.

### Reason

This was the only approach that could actually satisfy User Story 2's failure case as written: "attempting to remove a tag that does not exist on the task must return a validation error." That requires the API to know the caller's *intent* (add vs. remove) rather than just receiving a final tag list.

### Alternatives Suggested by AI

The AI explicitly called out the fork before implementation: "Simplest: treat `tags` on `TaskUpdate` as the full new tag list (client sends the complete desired set)... More faithful to the user story: add a separate field to `TaskUpdate`, e.g. `remove_tags: list[str] | None = None`, so the API can explicitly validate 'this tag must exist before removal.'"

### Rejected Alternative

The "simplest" option — clients send the complete desired tag list on every `PATCH`, and the server just replaces it — was rejected. With a full-replacement list, there's no way to distinguish "the caller tried to remove a tag that was never there" from "the caller just omitted it," so User Story 2's explicit validation-error requirement would silently stop working. It also pushes more responsibility onto every API caller (frontend included) to always know and resend a task's entire current tag set, which is unnecessary complexity outside what the user stories asked for.

### Consequences

**Advantage:** `add_tags`/`remove_tags` map directly onto the user stories' language ("add a tag", "remove a tag"), so the API errors match the acceptance criteria exactly, and partial updates never accidentally drop tags the caller didn't mean to touch.
**Limitation:** `update_task` now has to special-case `add_tags`/`remove_tags` outside the generic `payload.model_dump(exclude_unset=True)` merge that every other field uses, which is a small asymmetry a future contributor needs to know about before touching tag-update logic.
