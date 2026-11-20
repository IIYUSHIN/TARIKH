import { h, clear, fmtDate } from "./dom.js";
import { api } from "./api.js";
import { TXT, STATUS_WORD, NEEDS } from "./copy.js";

function complaintCell(w) {
  if (!w) return "";
  if (w.status === "unknown") return h("span", { class: "quiet" }, "Needs " + NEEDS.complaint);
  const cls = ["open", "closing", "expired"].includes(w.status) ? "stamp" : "stamp stamp--ok";
  if (w.status === "met") return h("span", { class: "quiet" }, "Met");
  return h("span", {}, h("span", { class: cls, style: "transform:none;margin:0 8px 0 0" }, STATUS_WORD[w.status]), h("span", { class: "mono" }, fmtDate(w.closes)));
}

export async function renderMatters(host) {
  clear(host);
  const title = h("h1", { class: "display" }, TXT.mattersTitle);
  const msg = h("div", { "aria-live": "polite" });
  const body = h("div");
  const input = h("input", { class: "input", id: "new-title", name: "title", autocomplete: "off" });
  const newForm = h("form", { class: "newform", hidden: true, onsubmit: async (e) => {
    e.preventDefault();
    try { const m = await api.newMatter(input.value || "Untitled matter"); location.hash = `#/m/${m.id}`; }
    catch (err) { clear(msg).append(h("p", { class: "err" }, err.message)); }
  } }, h("div", { class: "field" }, h("label", { class: "label", for: "new-title" }, TXT.newMatterLabel), input), h("button", { class: "btn btn--solid", type: "submit" }, TXT.createMatter));
  const sampleBtn = h("button", { class: "btn", type: "button", onclick: async (ev) => {
    const b = ev.currentTarget; b.disabled = true; b.textContent = "Reading the three sample papers";
    clear(msg).append(h("div", { class: "progress", role: "progressbar", "aria-label": "Reading the sample papers" }));
    try { const m = await api.sample(); location.hash = `#/m/${m.id}`; }
    catch (err) { b.disabled = false; b.textContent = TXT.openSample; clear(msg).append(h("p", { class: "err" }, err.message)); }
  } }, TXT.openSample);
  const newBtn = h("button", { class: "btn btn--solid", type: "button", onclick: () => { newForm.hidden = !newForm.hidden; if (!newForm.hidden) input.focus(); } }, TXT.newMatter);
  host.append(h("div", { class: "room__head", style: "margin-top:var(--s-6)" }, title, h("div", { style: "display:flex;gap:12px;flex-wrap:wrap" }, sampleBtn, newBtn)), newForm, msg, body);

  let list;
  try { list = await api.matters(); } catch (err) { body.append(h("p", { class: "err" }, err.message)); return; }
  if (!list.length) { body.append(h("p", { class: "empty" }, TXT.mattersEmpty)); return; }
  body.append(h("table", { class: "ledger-table" },
    h("thead", {}, h("tr", {}, ["Matter", "Papers", "Complaint window", "Brief"].map((x) => h("th", { scope: "col" }, x)))),
    h("tbody", {}, list.map((m) => h("tr", {}, h("td", {}, h("a", { class: "row-title", href: `#/m/${m.id}` }, m.title)),
      h("td", { class: "mono" }, `${m.documents} of 3`), h("td", {}, complaintCell(m.complaint)),
      h("td", {}, m.approved_by ? h("span", { class: "stamp stamp--ok", style: "transform:none" }, "Approved") : h("span", { class: "quiet" }, "Not approved")))))));
}
