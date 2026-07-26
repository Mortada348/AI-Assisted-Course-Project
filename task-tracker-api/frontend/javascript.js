const backendBaseUrl = "http://localhost:8000";
const tasks = [];
const statusColumns = ["ToDo", "InProgress", "Done"];
const priorityOrder = { High: 1, Medium: 2, Low: 3 };

let dragState = null;
let modalElements = {};
let currentTagFilter = null;
let modalTags = [];
let modalOriginalTags = [];
let removedTagsInSession = [];

function escapeText(value) {
  return String(value ?? "");
}

function sortTasks(taskList) {
  return [...taskList].sort((a, b) => {
    const priorityA = priorityOrder[a.priority] ?? Number.MAX_SAFE_INTEGER;
    const priorityB = priorityOrder[b.priority] ?? Number.MAX_SAFE_INTEGER;

    if (priorityA !== priorityB) {
      return priorityA - priorityB;
    }

    const idA = Number(a.id);
    const idB = Number(b.id);
    return Number.isFinite(idA) && Number.isFinite(idB)
      ? idA - idB
      : String(a.id).localeCompare(String(b.id));
  });
}

function getTomorrowDateString() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return date.toISOString().split("T")[0];
}

function createCard(task) {
  const card = document.createElement("li");
  card.className = "card";
  card.dataset.taskId = String(task.id);
  card.draggable = true;

  const title = document.createElement("h2");
  title.className = "card-title";
  title.textContent = escapeText(task.title || "Untitled task");
  card.appendChild(title);

  if (task.description) {
    const description = document.createElement("p");
    description.className = "card-description";
    description.textContent = escapeText(task.description);
    card.appendChild(description);
  }

  const meta = document.createElement("div");
  meta.className = "card-meta";

  const priority = document.createElement("span");
  priority.className = "badge badge--priority";
  priority.textContent = `${escapeText(task.priority || "Low")} priority`;
  meta.appendChild(priority);

  const assignee = document.createElement("span");
  assignee.className = "badge badge--assignee";
  assignee.textContent = escapeText(task.assignee || "Unassigned");
  meta.appendChild(assignee);

  if (task.due_date) {
    const dueDate = document.createElement("span");
    dueDate.className = "badge badge--due-date";
    dueDate.textContent = `Due ${escapeText(task.due_date)}`;
    meta.appendChild(dueDate);
  }

  const overdueBadge = document.createElement("span");
  overdueBadge.className = `badge ${task.is_overdue ? "badge--overdue" : "badge--not-overdue"}`;
  overdueBadge.textContent = task.is_overdue ? "Overdue" : "Not overdue";
  meta.appendChild(overdueBadge);

  if (task.is_overdue) {
    card.classList.add("card--overdue");
  }

  card.appendChild(meta);

  if (task.tags && task.tags.length > 0) {
    const tagsDiv = document.createElement("div");
    tagsDiv.className = "card-tags";
    task.tags.forEach((tag) => {
      const tagChip = document.createElement("span");
      tagChip.className = "tag-chip";
      tagChip.textContent = escapeText(tag);
      tagsDiv.appendChild(tagChip);
    });
    card.appendChild(tagsDiv);
  }

  const actions = document.createElement("div");
  actions.className = "card-actions";

  const editButton = document.createElement("button");
  editButton.className = "button";
  editButton.type = "button";
  editButton.textContent = "Edit";
  editButton.addEventListener("click", () => openModal("edit", task));
  actions.appendChild(editButton);

  card.appendChild(actions);

  card.addEventListener("dragstart", onCardDragStart);
  card.addEventListener("dragend", onCardDragEnd);

  return card;
}

function renderBoard(currentTasks) {
  const rawTasks = Array.isArray(currentTasks) ? currentTasks : [];
  const noResultsMsg = document.getElementById("no-results-message");

  if (currentTagFilter && rawTasks.length === 0) {
    noResultsMsg.classList.remove("hidden");
  } else {
    noResultsMsg.classList.add("hidden");
  }

  const grouped = {
    ToDo: [],
    InProgress: [],
    Done: [],
  };

  rawTasks.forEach((task) => {
    if (statusColumns.includes(task.status)) {
      grouped[task.status].push(task);
    }
  });

  statusColumns.forEach((status) => {
    const column = document.querySelector(`.column[data-status="${status}"]`);
    if (!column) {
      return;
    }

    const cardList = column.querySelector(".card-list");
    const countLabel = column.querySelector(".column-count");
    if (!cardList || !countLabel) {
      return;
    }

    cardList.innerHTML = "";
    const sortedTasks = sortTasks(grouped[status]);

    sortedTasks.forEach((task) => {
      cardList.appendChild(createCard(task));
    });

    countLabel.textContent = `${sortedTasks.length} task${sortedTasks.length === 1 ? "" : "s"}`;
  });

  attachColumnDragListeners();
}

function attachColumnDragListeners() {
  document.querySelectorAll(".column").forEach((column) => {
    column.addEventListener("dragover", onColumnDragOver);
    column.addEventListener("drop", onColumnDrop);
    column.addEventListener("dragleave", onColumnDragLeave);
  });
}

function onCardDragStart(event) {
  const card = event.currentTarget;
  const taskId = card.dataset.taskId;
  const currentStatus = card.closest("[data-status]")?.dataset.status;

  dragState = { taskId, currentStatus };
  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData("text/html", card.innerHTML);
  card.classList.add("card--dragging");
}

function onCardDragEnd(event) {
  const card = event.currentTarget;
  card.classList.remove("card--dragging");
  dragState = null;
}

function onColumnDragOver(event) {
  if (!dragState) return;
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  event.currentTarget.classList.add("column--drag-over");
}

function onColumnDragLeave(event) {
  if (event.currentTarget === event.target) {
    event.currentTarget.classList.remove("column--drag-over");
  }
}

async function onColumnDrop(event) {
  event.preventDefault();
  const column = event.currentTarget;
  column.classList.remove("column--drag-over");

  if (!dragState) return;

  const { taskId, currentStatus } = dragState;
  const targetStatus = column.dataset.status;

  if (targetStatus === currentStatus) {
    return;
  }

  const taskIndex = tasks.findIndex((t) => String(t.id) === taskId);
  if (taskIndex === -1) {
    console.error(`Task ${taskId} not found in state`);
    dragState = null;
    return;
  }

  const originalTask = { ...tasks[taskIndex] };

  tasks[taskIndex].status = targetStatus;
  renderBoard(tasks);

  try {
    const patchBody = { status: targetStatus };
    console.log(
      `[PATCH /tasks/${taskId}] Sending:`,
      JSON.stringify(patchBody, null, 2),
    );
    console.log(
      `[PATCH /tasks/${taskId}] Full task object:`,
      JSON.stringify(tasks[taskIndex], null, 2),
    );

    const response = await fetch(`${backendBaseUrl}/tasks/${taskId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patchBody),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage =
        errorData.detail || `Server error: ${response.status}`;
      throw new Error(errorMessage);
    }
  } catch (error) {
    tasks[taskIndex] = originalTask;
    renderBoard(tasks);

    const fallbackMsg =
      error instanceof TypeError
        ? "Network error. Card moved back."
        : error.message;
    alert(`Failed to update task: ${fallbackMsg}`);
  }

  dragState = null;
}

function clearModalErrors() {
  modalElements.titleError.classList.add("hidden");
  modalElements.dueDateError.classList.add("hidden");
  modalElements.formError.classList.add("hidden");
  modalElements.formError.textContent = "";
  modalElements.tagError.classList.add("hidden");
  modalElements.tagError.textContent = "";
}

function renderModalTags() {
  const container = modalElements.tagsContainer;
  container.innerHTML = "";

  modalTags.forEach((tag, index) => {
    const chip = document.createElement("span");
    chip.className = "tag-chip";
    chip.dataset.index = index;

    const isNewTag = !modalOriginalTags.includes(tag);
    if (isNewTag) {
      chip.classList.add("new");
    }

    const label = document.createElement("span");
    label.textContent = escapeText(tag);
    chip.appendChild(label);

    const removeBtn = document.createElement("button");
    removeBtn.className = "tag-chip-remove";
    removeBtn.type = "button";
    removeBtn.textContent = "×";
    removeBtn.addEventListener("click", (e) => {
      e.preventDefault();
      removeModalTag(index);
    });
    chip.appendChild(removeBtn);

    container.appendChild(chip);
  });
}

function addModalTag(tagValue) {
  const trimmed = tagValue.trim();

  if (!trimmed) {
    modalElements.tagError.textContent = "Tag cannot be empty";
    modalElements.tagError.classList.remove("hidden");
    return false;
  }

  const normalized = trimmed.toLowerCase();
  if (modalTags.some((t) => t.toLowerCase() === normalized)) {
    modalElements.tagError.textContent = "Duplicate tag (case-insensitive)";
    modalElements.tagError.classList.remove("hidden");
    return false;
  }

  modalElements.tagError.classList.add("hidden");
  modalElements.tagError.textContent = "";
  modalTags.push(trimmed);
  renderModalTags();
  modalElements.tagInput.value = "";
  return true;
}

function removeModalTag(index) {
  const tag = modalTags[index];
  if (modalOriginalTags.includes(tag)) {
    removedTagsInSession.push(tag);
  }
  modalTags.splice(index, 1);
  renderModalTags();
}

function openModal(mode, task = null) {
  modalElements.overlay.classList.remove("hidden");
  modalElements.form.dataset.mode = mode;
  modalElements.modalTitle.textContent =
    mode === "edit" ? "Edit Task" : "New Task";
  clearModalErrors();

  modalElements.dueDateInput.min = getTomorrowDateString();

  modalTags = [];
  modalOriginalTags = [];
  removedTagsInSession = [];

  if (mode === "edit" && task) {
    modalElements.taskIdInput.value = String(task.id);
    modalElements.titleInput.value = task.title || "";
    modalElements.descriptionInput.value = task.description || "";
    modalElements.statusInput.value = task.status || "ToDo";
    modalElements.priorityInput.value = task.priority || "Low";
    modalElements.assigneeInput.value = task.assignee || "";
    modalElements.dueDateInput.value = task.due_date || "";
    modalOriginalTags = task.tags ? [...task.tags] : [];
    modalTags = [...modalOriginalTags];
  } else {
    modalElements.form.reset();
    modalElements.taskIdInput.value = "";
    modalElements.statusInput.value = "ToDo";
    modalElements.priorityInput.value = "Low";
    modalElements.dueDateInput.value = "";
  }

  renderModalTags();
  modalElements.titleInput.focus();
}

function closeModal() {
  modalElements.overlay.classList.add("hidden");
  modalElements.form.reset();
  clearModalErrors();
  modalTags = [];
  modalOriginalTags = [];
  removedTagsInSession = [];
  renderModalTags();
}

function setFormError(message) {
  modalElements.formError.textContent = message;
  modalElements.formError.classList.remove("hidden");
}

async function handleModalSubmit(event) {
  event.preventDefault();
  clearModalErrors();

  const taskId = modalElements.taskIdInput.value;
  const title = modalElements.titleInput.value.trim();
  const description = modalElements.descriptionInput.value.trim();
  const status = modalElements.statusInput.value;
  const priority = modalElements.priorityInput.value;
  const assigneeRaw = modalElements.assigneeInput.value.trim();
  const assignee = assigneeRaw === "" ? null : assigneeRaw;
  const dueDate = modalElements.dueDateInput.value;

  if (!title) {
    modalElements.titleError.classList.remove("hidden");
    return;
  }

  if (!dueDate) {
    modalElements.dueDateError.classList.remove("hidden");
    return;
  }

  const payload = {
    title,
    description,
    status,
    priority,
    assignee,
    due_date: dueDate,
  };

  const mode = modalElements.form.dataset.mode === "edit" ? "edit" : "create";

  if (mode === "create") {
    payload.tags = modalTags;
  } else if (mode === "edit") {
    payload.add_tags = modalTags.filter((t) => !modalOriginalTags.includes(t));
    payload.remove_tags = removedTagsInSession;
  }

  const url =
    mode === "edit"
      ? `${backendBaseUrl}/tasks/${taskId}`
      : `${backendBaseUrl}/tasks`;
  const method = mode === "edit" ? "PATCH" : "POST";

  try {
    const response = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.status === 422) {
      const errorData = await response.json().catch(() => ({}));
      setFormError(errorData.detail || "Validation failed.");
      return;
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error: ${response.status}`);
    }

    closeModal();
    await fetchTasks();
  } catch (error) {
    setFormError(error.message || "Unable to save task.");
  }
}

function openModalForCreate() {
  openModal("create");
}

function setupModal() {
  modalElements = {
    overlay: document.getElementById("task-modal-overlay"),
    modalTitle: document.getElementById("task-modal-title"),
    form: document.getElementById("task-form"),
    titleInput: document.getElementById("task-title"),
    descriptionInput: document.getElementById("task-description"),
    statusInput: document.getElementById("task-status"),
    priorityInput: document.getElementById("task-priority"),
    assigneeInput: document.getElementById("task-assignee"),
    dueDateInput: document.getElementById("task-due-date"),
    dueDateError: document.getElementById("due-date-error"),
    filterOverdueInput: document.getElementById("filter-overdue"),
    taskIdInput: document.querySelector("input[name='taskId']"),
    titleError: document.getElementById("title-error"),
    formError: document.getElementById("modal-form-error"),
    tagInput: document.getElementById("task-tag-input"),
    tagAddButton: document.getElementById("tag-add-button"),
    tagsContainer: document.getElementById("task-tags-container"),
    tagError: document.getElementById("tag-error"),
  };

  document
    .getElementById("new-task-button")
    .addEventListener("click", openModalForCreate);
  document
    .getElementById("task-modal-close")
    .addEventListener("click", closeModal);
  document
    .getElementById("modal-cancel-button")
    .addEventListener("click", closeModal);
  modalElements.tagAddButton.addEventListener("click", (e) => {
    e.preventDefault();
    addModalTag(modalElements.tagInput.value);
  });
  modalElements.tagInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addModalTag(modalElements.tagInput.value);
    }
  });
  modalElements.overlay.addEventListener("click", (event) => {
    if (event.target === modalElements.overlay) {
      closeModal();
    }
  });
  modalElements.form.addEventListener("submit", handleModalSubmit);
  modalElements.filterOverdueInput.addEventListener("change", fetchTasks);
  document.addEventListener("keydown", (event) => {
    if (
      event.key === "Escape" &&
      !modalElements.overlay.classList.contains("hidden")
    ) {
      closeModal();
    }
  });
}

async function fetchTasks() {
  try {
    const params = new URLSearchParams();
    if (modalElements.filterOverdueInput.checked) {
      params.set("not_overdue", "true");
    }
    if (currentTagFilter) {
      params.set("tag", currentTagFilter);
    }
    const url = `${backendBaseUrl}/tasks${params.toString() ? `?${params}` : ""}`;
    console.log(`[GET /tasks] Fetching from ${url}`);
    const response = await fetch(url);
    console.log(`[GET /tasks] Response status: ${response.status}`);

    if (!response.ok) {
      throw new Error(`Failed to load tasks: ${response.status}`);
    }

    const data = await response.json();
    console.log(`[GET /tasks] Received tasks:`, JSON.stringify(data, null, 2));

    tasks.length = 0;
    if (Array.isArray(data)) {
      tasks.push(...data);
    }

    updateTagFilterUI();
    renderBoard(tasks);
  } catch (error) {
    console.error("Task loading error:", error);
    renderBoard(tasks);
  }
}

function extractAvailableTags() {
  const tagsSet = new Set();
  tasks.forEach((task) => {
    if (task.tags && Array.isArray(task.tags)) {
      task.tags.forEach((tag) => {
        tagsSet.add(tag);
      });
    }
  });
  return Array.from(tagsSet).sort();
}

function updateTagFilterUI() {
  const container = document.getElementById("tag-filter-container");
  container.innerHTML = "";

  const availableTags = extractAvailableTags();

  availableTags.forEach((tag) => {
    const chip = document.createElement("button");
    chip.className = "tag-filter-chip";
    chip.type = "button";
    chip.textContent = escapeText(tag);

    if (currentTagFilter === tag) {
      chip.classList.add("active");
    }

    chip.addEventListener("click", () => {
      currentTagFilter = tag;
      fetchTasks();
    });

    container.appendChild(chip);
  });
}

function clearTagFilter() {
  currentTagFilter = null;
  fetchTasks();
}

function init() {
  setupModal();
  document
    .getElementById("clear-tag-filter-button")
    .addEventListener("click", clearTagFilter);
  fetchTasks();
}

document.addEventListener("DOMContentLoaded", init);
