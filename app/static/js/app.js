// Todo App - Frontend Logic

const API_URL = "/api/todos";

const todoForm = document.getElementById("todo-form");
const todoInput = document.getElementById("todo-input");
const todoList = document.getElementById("todo-list");
const emptyState = document.getElementById("empty-state");
const errorState = document.getElementById("error-state");
const listContainer = document.getElementById("todo-list-container");

let todos = [];

async function fetchTodos() {
  listContainer.classList.add("loading");
  errorState.hidden = true;
  try {
    const res = await fetch(API_URL + "/");
    if (!res.ok) throw new Error("서버 오류");
    todos = await res.json();
    renderTodos();
  } catch {
    errorState.hidden = false;
    emptyState.hidden = true;
    todoList.innerHTML = "";
  } finally {
    listContainer.classList.remove("loading");
  }
}

async function addTodo(title) {
  const res = await fetch(API_URL + "/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("추가 실패");
  const todo = await res.json();
  todos.push(todo);
  renderTodos();
}

async function toggleTodo(id, completed) {
  const todo = todos.find((t) => t.id === id);
  if (!todo) return;

  // Optimistic update
  const prevCompleted = todo.completed;
  const prevCompletedAt = todo.completed_at;
  todo.completed = completed;
  todo.completed_at = completed ? new Date().toISOString().replace("T", " ").slice(0, 19) : null;
  renderTodos();

  try {
    const res = await fetch(`${API_URL}/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ completed }),
    });
    if (!res.ok) throw new Error("토글 실패");
    const updated = await res.json();
    Object.assign(todo, updated);
    renderTodos();
  } catch {
    // Rollback
    todo.completed = prevCompleted;
    todo.completed_at = prevCompletedAt;
    renderTodos();
  }
}

async function deleteTodo(id) {
  const res = await fetch(`${API_URL}/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("삭제 실패");
  todos = todos.filter((t) => t.id !== id);
  renderTodos();
}

async function updateTodoTitle(id, title) {
  const res = await fetch(`${API_URL}/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("수정 실패");
  const updated = await res.json();
  const todo = todos.find((t) => t.id === id);
  if (todo) Object.assign(todo, updated);
  renderTodos();
}

function formatDatetime(isoStr) {
  if (!isoStr) return null;
  // SQLite returns "YYYY-MM-DD HH:MM:SS" — display as-is
  return isoStr.replace("T", " ").slice(0, 19);
}

function formatMeta(todo) {
  const created = formatDatetime(todo.created_at);
  const completed = formatDatetime(todo.completed_at);
  if (completed) {
    return `추가: ${created}  |  완료: ${completed}`;
  }
  return `추가: ${created}`;
}

function renderTodos() {
  todoList.innerHTML = "";
  const hasTodos = todos.length > 0;
  emptyState.hidden = hasTodos;
  errorState.hidden = true;

  todos.forEach((todo) => {
    const li = createTodoElement(todo);
    todoList.appendChild(li);
  });
}

function createTodoElement(todo) {
  const li = document.createElement("li");
  li.className = "todo-item" + (todo.completed ? " completed" : "");
  li.dataset.id = todo.id;

  // Checkbox
  const checkbox = document.createElement("div");
  checkbox.className = "todo-checkbox";
  checkbox.setAttribute("role", "checkbox");
  checkbox.setAttribute("aria-checked", String(todo.completed));
  checkbox.setAttribute("tabindex", "0");

  const checkMark = document.createElement("span");
  checkMark.className = "todo-checkbox-mark";
  checkMark.innerHTML = "&#10003;";
  checkbox.appendChild(checkMark);

  // Body (title + meta)
  const body = document.createElement("div");
  body.className = "todo-body";

  const titleSpan = document.createElement("span");
  titleSpan.className = "todo-title";
  titleSpan.textContent = todo.title;

  const meta = document.createElement("span");
  meta.className = "todo-meta";
  meta.textContent = formatMeta(todo);

  body.appendChild(titleSpan);
  body.appendChild(meta);

  // Delete button
  const deleteBtn = document.createElement("button");
  deleteBtn.className = "todo-delete";
  deleteBtn.setAttribute("aria-label", "삭제");
  deleteBtn.innerHTML = "&times;";

  li.appendChild(checkbox);
  li.appendChild(body);
  li.appendChild(deleteBtn);

  // Event handlers
  checkbox.addEventListener("click", () => handleToggle(todo));
  checkbox.addEventListener("keydown", (e) => {
    if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      handleToggle(todo);
    }
  });

  deleteBtn.addEventListener("click", () => handleDelete(li, todo.id));

  titleSpan.addEventListener("dblclick", () => startEditing(li, todo));

  return li;
}

function handleToggle(todo) {
  const newCompleted = !todo.completed;
  toggleTodo(todo.id, newCompleted);
}

function handleDelete(li, id) {
  li.classList.add("removing");
  li.addEventListener(
    "transitionend",
    async () => {
      try {
        await deleteTodo(id);
      } catch {
        li.classList.remove("removing");
      }
    },
    { once: true }
  );
}

function startEditing(li, todo) {
  if (todo.completed) return;

  const titleSpan = li.querySelector(".todo-title");
  const originalTitle = todo.title;

  const input = document.createElement("input");
  input.type = "text";
  input.className = "todo-edit-input";
  input.value = originalTitle;

  li.replaceChild(input, titleSpan);
  input.focus();
  input.select();

  let saved = false;

  async function save() {
    if (saved) return;
    saved = true;
    const newTitle = input.value.trim();
    if (!newTitle || newTitle === originalTitle) {
      cancel();
      return;
    }
    try {
      await updateTodoTitle(todo.id, newTitle);
    } catch {
      cancel();
    }
  }

  function cancel() {
    if (li.contains(input)) {
      li.replaceChild(titleSpan, input);
    }
  }

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      save();
    } else if (e.key === "Escape") {
      saved = true;
      cancel();
    }
  });

  input.addEventListener("blur", save);
}

todoForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = todoInput.value.trim();
  if (!title) {
    todoInput.classList.add("shake");
    todoInput.addEventListener("animationend", () => todoInput.classList.remove("shake"), { once: true });
    return;
  }
  try {
    await addTodo(title);
    todoInput.value = "";
    todoInput.focus();
  } catch {
    // Silently handle — server validation covers this
  }
});

fetchTodos();
