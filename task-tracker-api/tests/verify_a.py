from datetime import date, timedelta
from pydantic import ValidationError
from app.models import TaskCreate, TaskUpdate, TaskStatus, TaskPriority
def expect_fail(label, fn):
  try:
    fn()
    print(f"FAIL: {label} — value was accepted but should have been rejected")
  except ValidationError:
    print(f"PASS: {label}")
def expect_ok(label, fn):
  try:
    fn()
    print(f"PASS: {label}")
  except Exception as e:
    print(f"FAIL: {label} — {e}")
# 1. Whitespace title rejected
expect_fail("whitespace title rejected", lambda: TaskCreate(title=" "))
# 2. Empty title rejected
expect_fail("empty title rejected", lambda: TaskCreate(title=""))
# 3. Title over 200 chars rejected
expect_fail("title > 200 chars rejected", lambda: TaskCreate(title="x" * 201))
# 4. Valid title accepted, defaults applied
def _ok_defaults():
  t = TaskCreate(title="Hello")
  assert t.status == TaskStatus.TODO
  assert t.priority == TaskPriority.MEDIUM
  assert t.description == ""
  assert t.assignee is None

expect_ok("defaults applied (status=ToDo, priority=Medium, description='')",
_ok_defaults)
# 5. extra='forbid' — unknown field rejected on TaskCreate
expect_fail("extra field rejected on TaskCreate", lambda: TaskCreate(title="x",
made_up="value"))
# 6. id NOT settable via TaskCreate
expect_fail("id rejected on TaskCreate", lambda: TaskCreate(title="x", id="abc"))
# 7. created_at NOT settable via TaskUpdate
expect_fail("created_at rejected on TaskUpdate", lambda: TaskUpdate(created_at="2025-01-01T00:00:00Z"))
# 8. Invalid enum value rejected
expect_fail("invalid status rejected", lambda: TaskCreate(title="x", status="Whatever"))
# 9. due_date today rejected on TaskCreate
expect_fail("due_date today rejected on TaskCreate", lambda: TaskCreate(title="x", due_date=date.today()))
# 10. due_date past rejected on TaskCreate
expect_fail("due_date past rejected on TaskCreate", lambda: TaskCreate(title="x", due_date=date.today() - timedelta(days=1)))
# 11. due_date future accepted on TaskCreate
expect_ok("due_date future accepted on TaskCreate", lambda: TaskCreate(title="x", due_date=date.today() + timedelta(days=1)))
# 12. due_date today rejected on TaskUpdate
expect_fail("due_date today rejected on TaskUpdate", lambda: TaskUpdate(due_date=date.today()))
# 13. due_date past rejected on TaskUpdate
expect_fail("due_date past rejected on TaskUpdate", lambda: TaskUpdate(due_date=date.today() - timedelta(days=1)))
# 14. due_date future accepted on TaskUpdate
expect_ok("due_date future accepted on TaskUpdate", lambda: TaskUpdate(due_date=date.today() + timedelta(days=1)))
# 15. blank tag rejected on TaskCreate
expect_fail("blank tag rejected on TaskCreate", lambda: TaskCreate(title="x", tags=[""]))
# 16. blank tag rejected on TaskUpdate add_tags
expect_fail("blank tag rejected on TaskUpdate add_tags", lambda: TaskUpdate(add_tags=["  "]))
# 17. duplicate tags deduplicated on TaskCreate, first casing preserved
def _ok_create_duplicate_tags():
  t = TaskCreate(title="x", tags=["Backend", "backend"])
  assert len(t.tags) == 1
  assert t.tags[0] == "Backend"

expect_ok("duplicate tags deduplicated on TaskCreate", _ok_create_duplicate_tags)
# 18. duplicate add_tags deduplicated on TaskUpdate, first casing preserved
def _ok_update_duplicate_add_tags():
  t = TaskUpdate(add_tags=["Backend", "backend"])
  assert len(t.add_tags) == 1
  assert t.add_tags[0] == "Backend"

expect_ok("duplicate add_tags deduplicated on TaskUpdate", _ok_update_duplicate_add_tags)
# 19. single valid tag trimmed and stored on TaskCreate
def _ok_create_single_tag_trimmed():
  t = TaskCreate(title="x", tags=[" backend "])
  assert t.tags == ["backend"]

expect_ok("single valid tag accepted and trimmed on TaskCreate", _ok_create_single_tag_trimmed)
# 20. multiple distinct valid tags preserved on TaskCreate
def _ok_create_multiple_tags():
  t = TaskCreate(title="x", tags=["backend", "frontend", "QA"])
  assert t.tags == ["backend", "frontend", "QA"]

expect_ok("multiple distinct tags accepted on TaskCreate", _ok_create_multiple_tags)
# 21. TaskCreate defaults tags to empty list when none provided
def _ok_create_default_tags_empty():
  t = TaskCreate(title="x")
  assert t.tags == []

expect_ok("TaskCreate without tags defaults to empty list", _ok_create_default_tags_empty)
# 22. valid remove_tags accepted on TaskUpdate
expect_ok("valid remove_tags accepted on TaskUpdate", lambda: TaskUpdate(remove_tags=["backend", "frontend"]))
# 23. blank tag rejected on TaskUpdate remove_tags
expect_fail("blank tag rejected on TaskUpdate remove_tags", lambda: TaskUpdate(remove_tags=[""]))
# 24. extra='forbid' still rejects unknown field alongside tags
expect_fail("extra field rejected on TaskCreate with tags", lambda: TaskCreate(title="x", tags=["backend"], made_up="value"))
print("--- Part A verifications complete ---")
print("--- Part B verifications complete ---")