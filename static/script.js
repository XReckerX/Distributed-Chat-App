const username = document.body.dataset.username;
const socket = io();
let selectedRecipient = null;
const messagesEl = document.getElementById("messages");
const userList = document.getElementById("userList");
const input = document.getElementById("messageInput");
const targetLabel = document.getElementById("targetLabel");
const clearTarget = document.getElementById("clearTarget");

function avatar(name) {
  return (name || "?").slice(0, 1).toUpperCase();
}

function timeText(iso) {
  try {
    return new Date(iso).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"});
  } catch { return ""; }
}

function addMessage(m, system=false) {
  const row = document.createElement("div");
  row.className = system ? "message system" : "message " + (m.sender === username ? "mine" : "theirs");

  if (system) {
    row.innerHTML = `<div>${escapeHtml(m.text)}</div>`;
  } else {
    const scope = m.recipient ? `Private · ${escapeHtml(m.recipient === username ? m.sender : m.recipient)}` : "Global";
    row.innerHTML = `
      <div class="msg-avatar">${escapeHtml(avatar(m.sender))}</div>
      <div class="msg-body">
        <div class="msg-meta"><strong>${escapeHtml(m.sender)}</strong><span>${scope}</span><time>${timeText(m.created_at)}</time></div>
        <div class="bubble">${escapeHtml(m.body)}</div>
      </div>`;
  }
  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));
}

async function loadHistory() {
  const res = await fetch("/api/history");
  if (!res.ok) return;
  const history = await res.json();
  history.forEach(addMessage);
}

function renderUsers(users) {
  userList.innerHTML = "";
  document.getElementById("userCount").textContent = users.length;
  users.forEach(user => {
    const button = document.createElement("button");
    button.className = "user-item" + (user === selectedRecipient ? " selected" : "");
    button.innerHTML = `<span class="avatar mini">${escapeHtml(avatar(user))}</span><span><strong>${escapeHtml(user)}</strong><small>${user === username ? "You" : "Click for private chat"}</small></span>`;
    if (user !== username) button.onclick = () => selectRecipient(user);
    else button.disabled = true;
    userList.appendChild(button);
  });
}

function selectRecipient(user) {
  selectedRecipient = user;
  document.getElementById("chatTitle").textContent = "Private Chat";
  document.getElementById("chatSubtitle").textContent = `Messages are only visible to ${user} and you`;
  targetLabel.textContent = `Sending privately to ${user}`;
  clearTarget.classList.remove("hidden");
  document.querySelectorAll(".user-item").forEach(x => x.classList.remove("selected"));
}

function clearPrivate() {
  selectedRecipient = null;
  document.getElementById("chatTitle").textContent = "Global Chat";
  document.getElementById("chatSubtitle").textContent = "Broadcast message to all connected users";
  targetLabel.textContent = "Sending to everyone";
  clearTarget.classList.add("hidden");
}

clearTarget.onclick = clearPrivate;

document.getElementById("messageForm").addEventListener("submit", e => {
  e.preventDefault();
  const body = input.value.trim();
  if (!body) return;
  socket.emit("send_message", {body, recipient: selectedRecipient});
  input.value = "";
  input.focus();
});

input.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    document.getElementById("messageForm").requestSubmit();
  }
});

socket.on("connect", () => {
  document.getElementById("connectionText").textContent = "Connected";
  document.getElementById("connectionDot").classList.add("online");
});

socket.on("disconnect", () => {
  document.getElementById("connectionText").textContent = "Disconnected";
  document.getElementById("connectionDot").classList.remove("online");
});

socket.on("online_users", renderUsers);
socket.on("system_message", m => addMessage(m, true));
socket.on("new_message", addMessage);
socket.on("error_message", m => addMessage({text: "Error: " + m.text}, true));

document.getElementById("myAvatar").textContent = avatar(username);
loadHistory();
