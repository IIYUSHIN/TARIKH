// Tiny element builder. Text goes in as text nodes, never as HTML, so nothing from a scan or a transcript can inject markup.
export function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k === "class") el.className = v;
    else if (k === "dataset") Object.assign(el.dataset, v);
    else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, "");
    else el.setAttribute(k, v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid == null || kid === false) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return el;
}
export const svg = (tag, attrs = {}, ...kids) => {
  const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  kids.flat().forEach((k) => k && el.append(k));
  return el;
};
export const clear = (el) => { while (el.firstChild) el.removeChild(el.firstChild); return el; };

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
export function fmtDate(iso) {
  if (!iso) return "";
  const [y, m, d] = iso.split("-").map(Number);
  return `${d} ${MONTHS[m - 1]} ${y}`;
}
export function fmtStamp(isoTs) {
  if (!isoTs) return "";
  const d = new Date(isoTs);
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}, ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}
export function fmtMoney(v) {
  const n = Number(String(v ?? "").replace(/[^0-9.]/g, ""));
  if (!isFinite(n) || !n) return v ?? "";
  return "₹" + n.toLocaleString("en-IN");
}
export const todayIso = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
export const dayNumber = (iso) => { const [y, m, d] = iso.split("-").map(Number); return Math.round(Date.UTC(y, m - 1, d) / 86400000); };
export const isoFromDay = (n) => new Date(n * 86400000).toISOString().slice(0, 10);
