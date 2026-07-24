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