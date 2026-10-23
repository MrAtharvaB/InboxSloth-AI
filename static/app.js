const fileInput = document.querySelector("#chat-file");
const dropZone = document.querySelector("#drop-zone");
const fileName = document.querySelector("#file-name");
const generateButton = document.querySelector("#generate-button");
const sampleButton = document.querySelector("#sample-button");
const formMessage = document.querySelector("#form-message");
const results = document.querySelector("#results");
const statusPill = document.querySelector("#ai-status");
let selectedFile = null;

function setMessage(message = "", isError = true) {
  formMessage.textContent = message;
  formMessage.classList.toggle("error", Boolean(message) && isError);
}

function selectFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".txt")) {
    selectedFile = null;
    fileName.textContent = "No file selected";
    generateButton.disabled = true;
    setMessage("Please choose a plain-text .txt export.");
    return;
  }
  selectedFile = file;
  fileName.textContent = file.name;
  generateButton.disabled = false;
  setMessage("");
}

fileInput.addEventListener("change", () => selectFile(fileInput.files[0]));
["dragenter", "dragover"].forEach((eventName) => dropZone.addEventListener(eventName, (event) => {
  event.preventDefault();
  dropZone.classList.add("dragging");
}));
["dragleave", "drop"].forEach((eventName) => dropZone.addEventListener(eventName, (event) => {
  event.preventDefault();
  dropZone.classList.remove("dragging");
}));
dropZone.addEventListener("drop", (event) => selectFile(event.dataTransfer.files[0]));

sampleButton.addEventListener("click", async () => {
  try {
    const response = await fetch("/sample_chat.txt");
    if (!response.ok) throw new Error("Sample unavailable");
    selectFile(new File([await response.blob()], "sample_chat.txt", { type: "text/plain" }));
    setMessage("Sample chat loaded. Ready to generate.", false);
  } catch {
    setMessage("Could not load the sample chat. Please choose a .txt file.");
  }
});

generateButton.addEventListener("click", async () => {
  if (!selectedFile) return;
  const formData = new FormData();
  formData.append("file", selectedFile);
  generateButton.disabled = true;
  sampleButton.disabled = true;
  generateButton.innerHTML = '<span class="spinner"></span> Reading your chat...';
  setMessage("");
  try {
    const response = await fetch("/api/summarize", { method: "POST", body: formData });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || "The digest could not be generated.");
    renderDigest(body.digest);
  } catch (error) {
    setMessage(error.message);
  } finally {
    generateButton.disabled = false;
    sampleButton.disabled = false;
    generateButton.innerHTML = "Generate My Digest <span>→</span>";
  }
});

function renderDigest(digest) {
  document.querySelector("#summary").textContent = digest.summary;
  renderList("#key-points", digest.key_points, "No key points identified.");
  renderList("#announcements", digest.announcements, "Nothing identified in this chat.");
  renderList("#pending-decisions", digest.pending_decisions, "No pending decisions identified.");
  renderTasks(digest.tasks);
  renderDeadlines(digest.deadlines);
  document.querySelector("#generated-at").textContent = `Generated ${new Date().toLocaleString()} · dates below come from the chat`;
  results.classList.remove("hidden");
  results.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderList(selector, items, emptyText) {
  const list = document.querySelector(selector);
  list.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = emptyText;
    list.appendChild(empty);
    return;
  }
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  });
}

function renderTasks(tasks) {
  const container = document.querySelector("#tasks");
  container.replaceChildren();
  if (!tasks.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "No action items identified.";
    container.appendChild(empty);
    return;
  }
  tasks.forEach((task) => {
    const item = document.createElement("div");
    item.className = "task-item";
    const title = document.createElement("strong");
    title.textContent = task.task;
    const meta = document.createElement("span");
    meta.textContent = `${task.owner || "Unknown"} · ${task.deadline || "Not specified"} · ${task.priority || "Low"} priority`;
    item.append(title, meta);
    container.appendChild(item);
  });
}

function renderDeadlines(deadlines) {
  const container = document.querySelector("#deadlines");
  container.replaceChildren();
  if (!deadlines.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "No deadlines or events identified.";
    container.appendChild(empty);
    return;
  }
  deadlines.forEach((deadline) => {
    const item = document.createElement("div");
    item.className = "deadline-item";
    const event = document.createElement("strong");
    event.textContent = deadline.event;
    const date = document.createElement("span");
    date.textContent = deadline.date;
    item.append(event, date);
    container.appendChild(item);
  });
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const health = await response.json();
    statusPill.classList.toggle("ready", health.ollama_reachable && health.model_installed);
    statusPill.querySelector("span:last-child").textContent = health.model_installed ? "Local AI ready" : health.message;
  } catch {
    statusPill.querySelector("span:last-child").textContent = "Local AI unavailable";
  }
}

document.querySelector("#copy-button").addEventListener("click", async () => {
  const text = document.querySelector("#results").innerText;
  try {
    await navigator.clipboard.writeText(text);
    document.querySelector("#copy-button").textContent = "Copied ✓";
    setTimeout(() => { document.querySelector("#copy-button").textContent = "Copy Digest"; }, 1800);
  } catch {
    setMessage("Clipboard access was blocked. Select the briefing text and copy it manually.");
  }
});

checkHealth();
