"use strict";
const $ = id => document.getElementById(id);
const labels = {TODO: "待辦", IN_PROGRESS: "進行中", DONE: "已完成"};
let editing = null, cursor = null, tasks = [], busy = false, connected = false;
let connection = null;
function message(text, error = false) { $("message").textContent = text; $("message").className = error ? "error" : ""; }
async function api(path, method = "GET", body) {
  if (!connection) throw new Error("請先連接工作空間。");
  const base = connection.base;
  const result = await fetch(base + path, {method, headers: {"Authorization": "Bearer " + connection.token,
    ...(body ? {"Content-Type": "application/json"} : {})}, body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(25000)});
  const data = result.status === 204 ? null : await result.json();
  if (!result.ok) throw new Error(data?.error?.message || `HTTP ${result.status}`);
  return data;
}
async function action(fn) {
  if (busy) return;
  busy = true;
  document.querySelectorAll("button").forEach(b => b.disabled = true);
  message("處理中…");
  try { await fn(); message("已完成，工作空間已更新。"); }
  catch (err) { message(err.message || "連線失敗，請檢查 API。", true); }
  finally { busy = false; document.querySelectorAll("button").forEach(b => b.disabled = false); }
}
function requireConnection() { if (!connected) throw new Error("請先連接工作空間。"); }
function resetForm() { editing = null; $("task-form").reset(); $("form-heading").textContent = "新增任務"; $("cancel").hidden = true; }
async function load(append = false) {
  const data = await api("/tasks?limit=50" + (append && cursor ? "&cursor=" + encodeURIComponent(cursor) : ""));
  tasks = append ? [...tasks, ...data.items] : data.items;
  cursor = data.next_cursor;
  render();
}
function render() {
  const list = $("task-list"); list.replaceChildren(); $("count").textContent = tasks.length;
  $("more").hidden = !cursor;
  if (!tasks.length) { const p = document.createElement("p"); p.className = "empty"; p.textContent = "還沒有任務，從右側新增第一件事。"; list.append(p); }
  for (const task of tasks) {
    const card = document.createElement("article"); card.className = "task";
    const title = document.createElement("h3"); title.textContent = task.title;
    const description = document.createElement("p"); description.textContent = task.description;
    const controls = document.createElement("div"); controls.className = "task-controls";
    const status = document.createElement("select"); status.setAttribute("aria-label", task.title + "狀態");
    for (const [value, text] of Object.entries(labels)) { const o = document.createElement("option"); o.value = value; o.textContent = text; status.append(o); }
    status.value = task.status;
    status.onchange = () => action(async () => { try { await api("/tasks/" + task.task_id, "PATCH", {status: status.value}); await load(); } catch (e) { render(); throw e; } });
    const edit = document.createElement("button"); edit.textContent = "編輯"; edit.className = "edit";
    edit.onclick = () => { editing = task.task_id; $("title").value = task.title; $("description").value = task.description; $("status").value = task.status; $("form-heading").textContent = "編輯任務"; $("cancel").hidden = false; $("title").focus(); };
    const del = document.createElement("button"); del.textContent = "刪除"; del.className = "delete";
    del.onclick = () => { if (confirm("確定刪除此任務？")) action(async () => { await api("/tasks/" + task.task_id, "DELETE"); if (editing === task.task_id) resetForm(); await load(); }); };
    controls.append(status, edit, del); card.append(title, description, controls); list.append(card);
  }
}
$("connect").onclick = () => action(async () => {
  connected = false;
  connection = null; tasks = []; cursor = null; resetForm(); render();
  const url = new URL($("api").value.trim());
  const local = ["localhost", "127.0.0.1"].includes(url.hostname);
  if (url.protocol !== "https:" && !(local && url.protocol === "http:")) throw new Error("雲端 API 必須使用 HTTPS。");
  if (url.username || url.password || url.search || url.hash || url.pathname !== "/") throw new Error("請輸入不含路徑的 API 根位址。");
  connection = {base: url.origin, token: $("token").value};
  await load(); connected = true; resetForm();
});
$("task-form").onsubmit = event => { event.preventDefault(); action(async () => {
  requireConnection(); const data = {title: $("title").value, description: $("description").value, status: $("status").value};
  await api(editing ? "/tasks/" + editing : "/tasks", editing ? "PATCH" : "POST", data); resetForm(); await load();
}); };
$("cancel").onclick = resetForm;
$("more").onclick = () => action(() => load(true));
$("weather-form").onsubmit = event => { event.preventDefault(); action(async () => {
  requireConnection(); const data = await api("/weather?city=" + encodeURIComponent($("city").value));
  $("weather-result").textContent = `${data.city} · ${data.current.temperature_2m} ${data.units.temperature_2m} · 風速 ${data.current.wind_speed_10m} ${data.units.wind_speed_10m} · ${data.current.time} UTC`;
}); };
