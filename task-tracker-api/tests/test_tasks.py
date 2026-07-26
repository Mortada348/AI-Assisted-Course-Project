from datetime import date, timedelta

from app.models import TaskPriority, TaskStatus


def test_create_task_valid_returns_201_with_full_body(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Write tests",
            "description": "Cover all endpoints",
            "status": TaskStatus.TODO.value,
            "priority": TaskPriority.HIGH.value,
            "assignee": "alice",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Write tests"
    assert body["description"] == "Cover all endpoints"
    assert body["status"] == TaskStatus.TODO.value
    assert body["priority"] == TaskPriority.HIGH.value
    assert body["assignee"] == "alice"
    assert isinstance(body["id"], str)
    assert body["id"]
    assert body["created_at"]
    assert body["updated_at"]


def test_create_task_missing_title_returns_422(client):
    response = client.post("/tasks", json={"description": "no title"})

    assert response.status_code == 422


def test_create_task_blank_title_returns_422(client):
    response = client.post("/tasks", json={"title": "   "})

    assert response.status_code == 422


def test_create_task_invalid_priority_returns_422(client):
    response = client.post("/tasks", json={"title": "Valid title", "priority": "Urgent"})

    assert response.status_code == 422


def test_create_task_unknown_field_returns_422(client):
    response = client.post("/tasks", json={"title": "Valid title", "unknown": "value"})

    assert response.status_code == 422


def test_list_tasks_empty_returns_200_and_empty_list(client):
    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_filter_by_status_no_match_returns_200_and_empty_list(client):
    client.post("/tasks", json={"title": "Open task"})

    response = client.get("/tasks", params={"status": TaskStatus.DONE.value})

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_filter_by_priority_returns_only_matches(client):
    client.post("/tasks", json={"title": "High priority", "priority": TaskPriority.HIGH.value})
    client.post("/tasks", json={"title": "Low priority", "priority": TaskPriority.LOW.value})

    response = client.get("/tasks", params={"priority": TaskPriority.HIGH.value})

    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "High priority"
    assert tasks[0]["priority"] == TaskPriority.HIGH.value


def test_get_task_by_id_returns_task(client, created_task):
    response = client.get(f"/tasks/{created_task['id']}")

    assert response.status_code == 200
    assert response.json() == created_task


def test_get_task_by_id_not_found_returns_404_with_detail(client):
    response = client.get("/tasks/nonexistent-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id nonexistent-id not found"


def test_patch_partial_update_keeps_other_fields(client):
    create_response = client.post(
        "/tasks",
        json={
            "title": "Original title",
            "description": "Keep this",
            "priority": TaskPriority.LOW.value,
            "assignee": "bob",
        },
    )
    task = create_response.json()

    patch_response = client.patch(
        f"/tasks/{task['id']}",
        json={"title": "Updated title"},
    )

    assert patch_response.status_code == 200
    updated = patch_response.json()
    assert updated["title"] == "Updated title"
    assert updated["description"] == "Keep this"
    assert updated["status"] == TaskStatus.TODO.value
    assert updated["priority"] == TaskPriority.LOW.value
    assert updated["assignee"] == "bob"
    assert updated["id"] == task["id"]
    assert updated["created_at"] == task["created_at"]


def test_patch_not_found_returns_404(client):
    response = client.patch("/tasks/nonexistent-id", json={"title": "New title"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id nonexistent-id not found"


def test_patch_valid_transition_todo_to_inprogress_returns_200(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}",
        json={"status": TaskStatus.IN_PROGRESS.value},
    )

    assert response.status_code == 200
    assert response.json()["status"] == TaskStatus.IN_PROGRESS.value


def test_patch_invalid_transition_todo_to_done_returns_422(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}",
        json={"status": TaskStatus.DONE.value},
    )

    assert response.status_code == 422


def test_patch_same_status_returns_422(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}",
        json={"status": TaskStatus.TODO.value},
    )

    assert response.status_code == 422


def test_delete_existing_returns_204_no_body(client, created_task):
    response = client.delete(f"/tasks/{created_task['id']}")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_missing_returns_404(client):
    response = client.delete("/tasks/nonexistent-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id nonexistent-id not found"

def test_patch_unknown_field_returns_422(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}",
        json={"title": "Valid title", "extra": "value"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]


def test_create_task_due_date_today_returns_422(client):
    response = client.post(
        "/tasks",
        json={"title": "Valid title", "due_date": date.today().isoformat()},
    )

    assert response.status_code == 422


def test_create_task_due_date_in_the_past_returns_422(client):
    response = client.post(
        "/tasks",
        json={"title": "Valid title", "due_date": (date.today() - timedelta(days=1)).isoformat()},
    )

    assert response.status_code == 422


def test_create_task_due_date_in_the_future_returns_201_and_includes_due_date(client):
    future_date = date.today() + timedelta(days=7)
    response = client.post(
        "/tasks",
        json={"title": "Valid title", "due_date": future_date.isoformat()},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["due_date"] == future_date.isoformat()


def test_create_task_no_due_date_returns_201_and_due_date_is_null(client):
    response = client.post("/tasks", json={"title": "No due date"})

    assert response.status_code == 201
    body = response.json()
    assert body["due_date"] is None


def test_patch_due_date_today_returns_422(client):
    create_response = client.post("/tasks", json={"title": "Original title"})
    task = create_response.json()

    response = client.patch(
        f"/tasks/{task['id']}",
        json={"due_date": date.today().isoformat()},
    )

    assert response.status_code == 422


def test_patch_due_date_in_the_past_returns_422(client):
    create_response = client.post("/tasks", json={"title": "Original title"})
    task = create_response.json()

    response = client.patch(
        f"/tasks/{task['id']}",
        json={"due_date": (date.today() - timedelta(days=1)).isoformat()},
    )

    assert response.status_code == 422


def test_patch_due_date_in_the_future_returns_200_and_updates_due_date(client):
    create_response = client.post("/tasks", json={"title": "Original title"})
    task = create_response.json()
    future_date = date.today() + timedelta(days=10)

    response = client.patch(
        f"/tasks/{task['id']}",
        json={"due_date": future_date.isoformat()},
    )

    assert response.status_code == 200
    assert response.json()["due_date"] == future_date.isoformat()


def test_patch_partial_update_keeps_due_date_unchanged(client):
    due_date = (date.today() + timedelta(days=5)).isoformat()
    create_response = client.post(
        "/tasks",
        json={"title": "Original title", "due_date": due_date},
    )
    task = create_response.json()

    patch_response = client.patch(
        f"/tasks/{task['id']}",
        json={"title": "Updated title"},
    )

    assert patch_response.status_code == 200
    updated = patch_response.json()
    assert updated["title"] == "Updated title"
    assert updated["due_date"] == due_date


def test_list_tasks_not_overdue_filter_returns_only_tasks_with_due_dates_and_not_overdue(client):
    overdue_date = (date.today() - timedelta(days=1)).isoformat()
    future_date = (date.today() + timedelta(days=5)).isoformat()
    client.post("/tasks", json={"title": "Overdue task", "due_date": overdue_date})
    client.post("/tasks", json={"title": "Future task", "due_date": future_date})
    client.post("/tasks", json={"title": "No due date"})

    response = client.get("/tasks", params={"not_overdue": "true"})

    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Future task"


def test_list_tasks_not_overdue_filter_returns_empty_list_when_no_tasks_have_due_dates(client):
    client.post("/tasks", json={"title": "No due date 1"})
    client.post("/tasks", json={"title": "No due date 2"})

    response = client.get("/tasks", params={"not_overdue": "true"})

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_not_overdue_filter_includes_future_due_date_tasks(client):
    future_date = (date.today() + timedelta(days=3)).isoformat()
    client.post("/tasks", json={"title": "Future task", "due_date": future_date})

    response = client.get("/tasks", params={"not_overdue": "true"})

    assert response.status_code == 200
    assert response.json()[0]["due_date"] == future_date


def test_list_tasks_not_overdue_filter_includes_done_tasks_with_past_due_date(client):
    past_date = (date.today() - timedelta(days=2)).isoformat()
    create_response = client.post("/tasks", json={"title": "Completed task", "due_date": past_date})
    task = create_response.json()

    response = client.patch(
        f"/tasks/{task['id']}",
        json={"status": TaskStatus.IN_PROGRESS.value},
    )
    assert response.status_code == 200
    response = client.patch(
        f"/tasks/{task['id']}",
        json={"status": TaskStatus.DONE.value},
    )
    assert response.status_code == 200

    response = client.get("/tasks", params={"not_overdue": "true"})

    assert response.status_code == 200
    assert any(t["id"] == task["id"] for t in response.json())


def test_list_tasks_not_overdue_filter_combined_with_priority_returns_only_matching_tasks(client):
    future_date = (date.today() + timedelta(days=4)).isoformat()
    client.post(
        "/tasks",
        json={"title": "High task", "priority": TaskPriority.HIGH.value, "due_date": future_date},
    )
    client.post(
        "/tasks",
        json={"title": "Low task", "priority": TaskPriority.LOW.value, "due_date": future_date},
    )

    response = client.get(
        "/tasks",
        params={"not_overdue": "true", "priority": TaskPriority.HIGH.value},
    )

    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["priority"] == TaskPriority.HIGH.value
