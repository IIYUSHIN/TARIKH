import { h, svg, clear, fmtDate, fmtStamp, fmtMoney, todayIso } from "./dom.js";
import { api, ApiError } from "./api.js";
import { createClock } from "./clock.js";
import { createViewer } from "./viewer.js";
import { TXT, DOC_LABEL, ADD_LABEL, READING, DATE_KEYS, SAFEGUARDS, NEEDS } from "./copy.js";

const SHORT_DOC = { cheque: "Cheque", return_memo: "Memo", demand_notice: "Notice" };
const TICK = () => svg("svg", { class: "tick", viewBox: "0 0 16 16", "aria-hidden": "true", fill: "none", stroke: "currentColor", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round" }, svg("path", { d: "M2.5 8.8l3.6 3.4L13.4 3.8" }));
const room = (id, title, meta, ...kids) => h("section", { class: "room", id, "aria-labelledby": id + "-h" },
  h("div", { class: "room__head" }, h("h2", { class: "title", id: id + "-h" }, title), meta ? h("p", { class: "room__meta" }, meta) : null), ...kids);
const errBox = (e) => h("p", { class: "err", role: "alert" }, e instanceof ApiError ? e.message : "Something unexpected stopped this step. Reload the page and try again.");

export async function renderMatter(host, matterId, ctx) {
  clear(host);
  let data;
  try { data = await api.matter(matterId); }
  catch (e) { host.append(h("p", { class: "empty" }, e.status === 404 ? "That matter does not exist." : e.message), h("a", { href: "#/" }, "Back to matters")); return; }
  document.title = `${data.matter.title} · Tarikh`;
  let asOf = ctx.today, windows = data.windows, current = data.matter;
  const slotMsg = {}, slotBusy = {};
  const factById = () => Object.fromEntries(current.documents.flatMap((d) => d.facts.map((f) => [f.id, f])));

  // ---------- header + answer + clock ----------
  const answer = h("p", { class: "answer", "data-testid": "answer", "aria-live": "polite" });
  const clock = createClock({ realToday: ctx.today, onDate: (iso, { live }) => { asOf = iso; scheduleWindows(live ? 70 : 0); } });
  const head = h("div");
  function paintHead() {
    const sample = current.title.toLowerCase().includes("fictional sample");
    clear(head).append(
      h("p", { class: "crumb" }, h("a", { href: "#/" }, "Matters"), " / ", "this matter"),
      h("div", { style: "display:flex;gap:24px;align-items:baseline;justify-content:space-between;flex-wrap:wrap;margin-top:var(--s-2)" },
        h("h1", { class: "display", id: "matter-title" }, current.title),
        current.approved_by ? h("span", { class: "stamp stamp--ok" }, "Brief approved") : h("span", { class: "stamp stamp--quiet" }, "Brief not approved")),
      sample ? h("p", { class: "notice", style: "margin-top:var(--s-4)" }, TXT.sampleNote) : null);
  }
  function paintAnswer() {
    const w = Object.fromEntries(windows.map((x) => [x.key, x]));
    const c = w.complaint, d = (iso) => h("span", { class: "date" }, fmtDate(iso));
    clear(answer); answer.className = "answer";
    if (!c || c.status === "unknown") {
      answer.append("The complaint date cannot be worked out yet. Missing: ", NEEDS.complaint, ".");
    } else if (c.status === "expired") {
      answer.classList.add("answer--stamp"); answer.append(h("b", {}, "The complaint window has closed."), " It closed on ", d(c.closes), ".");
    } else if (c.status === "upcoming") {
      answer.append("The complaint window opens on ", d(c.opens), " and closes on ", d(c.closes), ".");
    } else {
      answer.classList.add("answer--stamp");
      answer.append(h("b", {}, "The complaint window is open."), " File by ", d(c.closes), c.days_left != null ? `, ${c.days_left} day${c.days_left === 1 ? "" : "s"} from ${asOf === ctx.today ? "today" : fmtDate(asOf)}.` : ".");
    }
    answer.append(h("span", { class: "hint", style: "display:block;font:400 var(--t-sm)/1.5 var(--sans);margin-top:var(--s-2)" }, "This is the earlier, safer date. ", TXT.confirmLaw));
  }
  let timer, abort;
  function scheduleWindows(delay) {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      abort?.abort(); abort = new AbortController();
      try { const r = await api.deadlines(matterId, asOf, abort.signal); windows = r.windows; paintAnswer(); clock.update(windows, asOf); }
      catch (e) { if (e.name !== "AbortError" && !(e instanceof DOMException)) toast(e.message); }
    }, delay);
  }
  const clockBlock = h("div", { class: "bleed" }, h("div", { class: "bleed__in" }, h("h2", { class: "sr" }, TXT.clock), clock.el));

  // ---------- papers ----------
  const viewer = createViewer({ matterId, fileUrl: api.fileUrl });
  const slotsHost = h("div", { class: "slots", style: "grid-template-columns:repeat(auto-fit,minmax(260px,1fr));column-gap:var(--s-6)" });
  function paintSlots() {
    clear(slotsHost);
    for (const type of ["cheque", "return_memo", "demand_notice"]) {
      const have = current.documents.filter((d) => d.doc_type === type);
      const input = h("input", { type: "file", accept: "image/png,image/jpeg,image/tiff,image/bmp,application/pdf", class: "sr", id: "up-" + type, tabindex: "-1", "aria-label": ADD_LABEL[type], onchange: () => input.files[0] && upload(type, input.files[0]) });
      const slot = h("div", { class: "slot", ondragover: (e) => { e.preventDefault(); slot.classList.add("drag"); }, ondragleave: () => slot.classList.remove("drag"),
        ondrop: (e) => { e.preventDefault(); slot.classList.remove("drag"); const f = e.dataTransfer.files[0]; f && upload(type, f); } },
        h("div", {}, h("div", { class: "slot__name" }, DOC_LABEL[type]), h("div", { class: "slot__file" }, have.length ? have.map((d) => d.filename).join(", ") : "Not added")),
        h("button", { class: "btn btn--small", type: "button", disabled: !!slotBusy[type], onclick: () => input.click() }, have.length ? "Add another" : ADD_LABEL[type]), input,
        slotBusy[type] ? h("div", { class: "slot__msg" }, h("div", { class: "hint" }, READING[type]), h("div", { class: "progress", role: "progressbar", "aria-label": READING[type] })) : null,
        slotMsg[type] ? h("div", { class: "slot__msg" }, slotMsg[type]) : null);
      slotsHost.append(slot);
    }
  }
  async function upload(type, file) {
    slotBusy[type] = true; slotMsg[type] = null; paintSlots();
    try {
      const r = await api.addDocument(matterId, type, file);
      slotMsg[type] = r.warnings.length ? h("p", { class: "notice" }, r.warnings.join(" ")) : null;
      current = (await api.matter(matterId)).matter; scheduleWindows(0);
      paintAll(); viewer.show(r.document.id, [], "");
    } catch (e) { slotMsg[type] = errBox(e); }
    slotBusy[type] = false; paintSlots();
  }

  // ---------- ledger ----------
  const ledgerHost = h("div", { "data-testid": "ledger" });
  function showOnPaper(f) {
    const poly = f.source?.polygon?.length >= 6 ? [f.source.polygon] : [];
    viewer.show(f.doc_id, poly, `${f.label}: ${f.value ?? "not read"}${f.confidence != null ? ` (read at ${Math.round(f.confidence * 100)}%)` : ""}`);
    if (matchMedia("(max-width:959px)").matches) viewer.el.scrollIntoView({ block: "start" });
  }
  async function saveFact(f, value, row) {
    const status = row.querySelector(".fact__status");
    status.textContent = "Saving";
    try {
      const updated = await api.patchFact(f.id, value || null, "Advocate");
      Object.assign(f, updated);
      status.textContent = "Saved";
      paintLedgerRow(row, f); scheduleWindows(0); paintBrief();
    } catch (e) { status.replaceChildren(errBox(e)); }
  }
  function factRow(f) {
    const date = DATE_KEYS.has(f.key);
    const id = "f-" + f.id;
    const input = h("input", { class: "input", id, type: date ? "date" : "text", value: f.value ?? "", autocomplete: "off", spellcheck: "false",
      "aria-describedby": id + "-d", onchange: (e) => saveFact(f, e.target.value.trim(), row) });
    const low = f.confidence != null && f.confidence < 0.7;
    const row = h("div", { class: `fact${f.manual ? " fact--manual" : ""}${!f.value ? " fact--empty" : ""}${low || f.flag ? " fact--low" : ""}`, "data-key": f.key },
      h("label", { class: "fact__label", for: id }, f.label), h("div", { class: "fact__val" }, input, h("div", { class: "fact__meta", id: id + "-d" })));
    paintLedgerRow(row, f); return row;
  }
  function paintLedgerRow(row, f) {
    const meta = row.querySelector(".fact__meta"); clear(meta);
    row.classList.toggle("fact--empty", !f.value);
    if (f.key === "amount_figures" && f.value) meta.append(h("span", { class: "mono" }, fmtMoney(f.value)));
    if (f.confidence != null && !f.manual) meta.append(h("span", { class: "mono" }, `Read at ${Math.round(f.confidence * 100)}%`));
    if (f.verified && f.value) meta.append(h("span", {}, TICK(), " ", TXT.checked));
    if (f.source?.polygon?.length >= 6) meta.append(h("button", { class: "linkbtn", type: "button", "aria-label": `${TXT.showOnPaper}: ${f.label}`, onclick: () => showOnPaper(f) }, TXT.showOnPaper));
    if (f.value && !f.verified) meta.append(h("button", { class: "linkbtn", type: "button", "aria-label": `${TXT.markChecked}: ${f.label}`, onclick: () => saveFact(f, f.value, row) }, TXT.markChecked));
    if (f.manual && !f.value) meta.append(h("span", {}, TXT.notOnPaper));
    meta.append(h("span", { class: "fact__status", role: "status" }));
    row.querySelector(".fact__flag")?.remove();
    if (f.flag) meta.after(h("p", { class: "fact__flag" }, f.flag));
  }
  function paintLedger() {
    clear(ledgerHost);
    if (!current.documents.length) { ledgerHost.append(h("p", { class: "empty" }, TXT.noFacts)); return; }
    for (const d of current.documents) {
      ledgerHost.append(h("div", { class: "docgroup" },
        h("div", { class: "docgroup__head" }, h("h3", { class: "label" }, DOC_LABEL[d.doc_type]), h("span", { class: "mono quiet", style: "font-size:var(--t-xs)" }, d.filename)),
        d.facts.map(factRow),
        d.observations.length ? h("div", { style: "margin-top:var(--s-4)" }, h("p", { class: "label" }, "Seen on the cheque image by the model"),
          d.observations.map((o) => h("div", { class: "obs" }, h("span", {}, o.label), h("span", { class: "obs__s" }, o.status), o.note ? h("span", { class: "obs__n" }, o.note) : null))) : null));
    }
  }

  // ---------- brief ----------
  const briefHost = h("div");
  const brief = () => current.brief;
  async function draft(btn) {
    btn.disabled = true; btn.textContent = "Drafting";
    const bar = h("div", { class: "progress", role: "progressbar", "aria-label": "Drafting the brief" }); btn.after(bar);
    try { current.brief = await api.brief(matterId); current.approved_by = null; current.approved_at = null; paintHead(); }
    catch (e) { toast(e instanceof ApiError ? e.message : "The brief could not be drafted."); }
    paintBrief();
  }
  function paintBrief() {
    clear(briefHost);
    const facts = Object.values(factById()), have = facts.filter((f) => f.value), unchecked = have.filter((f) => !f.verified).length;
    const hasCheque = current.documents.some((d) => d.doc_type === "cheque" && d.facts.some((f) => f.value));
    const b = brief();
    const draftBtn = h("button", { class: "btn" + (b ? "" : " btn--solid"), type: "button", disabled: !hasCheque, onclick: (e) => draft(e.currentTarget) }, b ? TXT.redraft : TXT.draftBrief);
    if (!b) { briefHost.append(h("p", { class: "empty" }, "No brief yet. It is drafted from the facts in the ledger, and every sentence cites the facts it rests on."), h("div", { class: "actions" }, draftBtn, !hasCheque ? h("span", { class: "why" }, TXT.needCheque) : null)); return; }
    const byId = factById(); let lastSection = null;
    const docType = Object.fromEntries(current.documents.map((d) => [d.id, d.doc_type]));
    const approved = !!current.approved_by;
    const memo = h("article", { class: "memo" + (approved ? " memo--approved" : ""), "data-testid": "brief" },
      h("div", { class: "memo__head" }, h("p", { class: "hint" }, TXT.draftedBy(b.model), " ", fmtStamp(b.drafted_at) + "."),
        h("p", { class: "hint" }, unchecked ? `${unchecked} fact${unchecked === 1 ? "" : "s"} not yet checked` : "Every fact checked")),
      b.claims.map((c) => {
        const secs = [];
        if (c.section && c.section !== lastSection) { secs.push(h("p", { class: "section" }, c.section.replace(/_/g, " "))); lastSection = c.section; }
        const chips = c.fact_ids.map((id) => byId[id]).filter(Boolean).map((f) => h("button", { class: "src", type: "button", title: `${f.label}: ${f.value}`,
          onclick: () => showOnPaper(f) }, `${SHORT_DOC[docType[f.doc_id]] ?? ""} · ${f.label} · ${String(f.value).slice(0, 22)}`));
        return [secs, h("p", { class: "reading" }, c.text, " ", chips)];
      }),
      b.flagged.length ? h("div", { class: "left-out" }, h("p", {}, "Left out because the papers do not support it:"), h("ul", {}, b.flagged.map((x) => h("li", {}, x)))) : null,
      approved ? h("p", { class: "hint", style: "margin-top:var(--s-5)" }, h("span", { class: "stamp stamp--ok" }, "Approved"), ` by ${current.approved_by}, ${fmtStamp(current.approved_at)}`) : null);
    briefHost.append(memo);
    const actions = h("div", { class: "actions" }); briefHost.append(actions);
    actions.append(draftBtn);
    if (approved) actions.append(h("span", { class: "why" }, TXT.redraftWarn));
    if (!approved) {
      const name = h("input", { class: "input", id: "adv", autocomplete: "name", oninput: () => sync() });
      const go = h("button", { class: "btn btn--solid", type: "button", onclick: () => approve(name.value, go) }, TXT.approve);
      const why = h("span", { class: "why", id: "adv-why", role: "status" });
      const sync = () => { const ok = name.value.trim().length > 0; go.disabled = !ok; why.textContent = ok ? "" : TXT.needName; };
      sync(); actions.append(h("div", { class: "field" }, h("label", { class: "label", for: "adv" }, TXT.reviewer), name), go, why);
    } else {
      const sel = h("select", { class: "select", id: "speak-loc", style: "width:auto" }, ctx.locales.map((l) => h("option", { value: l.locale, disabled: !l.available }, l.name + (l.available ? "" : " (not offered here)"))));
      const audio = h("div");
      const play = h("button", { class: "btn", type: "button", onclick: async (e) => { e.currentTarget.disabled = true;
        try { const blob = await api.speak(matterId, sel.value); clear(audio).append(h("audio", { controls: true, autoplay: true, src: URL.createObjectURL(blob), "aria-label": "Brief read aloud" })); }
        catch (er) { clear(audio).append(errBox(er)); } e.currentTarget.disabled = false; } }, TXT.readAloud);
      actions.append(h("div", { class: "field" }, h("label", { class: "label", for: "speak-loc" }, "Language"), sel), play, audio);
    }
  }
  async function approve(name, btn) {
    btn.disabled = true;
    try { const m = await api.approve(matterId, name.trim()); current.approved_by = m.approved_by; current.approved_at = m.approved_at; paintHead(); paintBrief(); loadAudit(); }
    catch (e) { toast(e.message); btn.disabled = false; }
  }

  // ---------- ask ----------
  const askOut = h("div", { class: "answer-box", "aria-live": "polite" });
  const q = h("input", { class: "input", id: "q", placeholder: TXT.askHint, autocomplete: "off" });
  const askForm = h("form", { class: "askrow", onsubmit: async (e) => {
    e.preventDefault(); if (!q.value.trim()) { clear(askOut).append(h("p", { class: "err" }, "Type a question first.")); return; }
    clear(askOut).append(h("div", { class: "progress", role: "progressbar", "aria-label": "Asking the desk" }));
    try {
      const r = await api.ask(matterId, q.value);
      clear(askOut).append(h("p", { class: "reading" }, r.text), h("p", { class: "hint", style: "margin-top:8px" }, "Answered by the matter's agent."),
        r.tool_calls.length ? h("details", { class: "calls" }, h("summary", {}, `How it was worked out (${r.tool_calls.length} lookup${r.tool_calls.length === 1 ? "" : "s"})`),
          r.tool_calls.map((t) => h("pre", {}, `${t.name}(${JSON.stringify(t.args)})\n${JSON.stringify(t.result, null, 2)}`))) : null);
    } catch (er) { clear(askOut).append(errBox(er)); }
  } }, h("div", { class: "field" }, h("label", { class: "label", for: "q" }, TXT.askLabel), q), h("button", { class: "btn btn--solid", type: "submit" }, TXT.askButton));

  // ---------- voice ----------
  const voiceOut = h("div"), voiceCtl = h("div", { class: "voice__ctl" });
  function maskedText(t) {
    const out = []; let last = 0;
    for (const m of t.matchAll(/\*{3,}|\[[A-Za-z_ ]+\]/g)) { out.push(t.slice(last, m.index), h("mark", { class: "masked" }, m[0])); last = m.index + m[0].length; }
    out.push(t.slice(last)); return out;
  }
  function paintTranscript(t) {
    clear(voiceOut); if (!t) return;
    const lang = t.language.split("-")[0];
    voiceOut.append(h("div", { class: "twin", "data-testid": "transcript" },
      h("div", { class: "twin__col" }, h("p", { class: "label" }, `What was said (${t.language})`), h("p", { class: "reading", lang }, t.text)),
      h("div", { class: "twin__col" }, h("p", { class: "label" }, "What the model is allowed to see"), h("p", { class: "reading", lang }, maskedText(t.redacted_text)))),
      t.key_phrases.length ? h("p", { class: "hint", style: "margin-top:var(--s-3)" }, "Key phrases: ", t.key_phrases.join(", ")) : null);
  }
  async function sendAudio(blob, name) {
    clear(voiceOut).append(h("p", { class: "hint" }, "Transcribing with Azure Speech, then masking personal details with Azure AI Language."), h("div", { class: "progress", role: "progressbar", "aria-label": "Transcribing" }));
    try { const t = await api.voice(matterId, blob, sel.value, name); current.transcript = t; paintTranscript(t); }
    catch (e) { clear(voiceOut).append(errBox(e)); }
  }
  const sel = h("select", { class: "select", id: "voice-loc" }, ctx.locales.map((l) => h("option", { value: l.locale, disabled: !l.available }, l.name + (l.available ? "" : " (not offered here)"))));
  let rec = null;
  const recBtn = h("button", { class: "btn", type: "button", onclick: async () => {
    if (rec) { rec.stop(); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const chunks = []; rec = new MediaRecorder(stream);
      rec.ondataavailable = (e) => chunks.push(e.data);
      rec.onstop = () => { stream.getTracks().forEach((t) => t.stop()); const type = rec.mimeType || "audio/webm"; rec = null; recBtn.replaceChildren(TXT.record); sendAudio(new Blob(chunks, { type }), "voice-note"); };
      rec.start(); recBtn.replaceChildren(h("span", { class: "rec", "aria-hidden": "true" }), TXT.stop);
    } catch { clear(voiceOut).append(h("p", { class: "err" }, "The microphone is not available. Allow it in the browser, or upload a recording instead.")); }
  } }, TXT.record);
  const file = h("input", { type: "file", accept: "audio/*", class: "sr", id: "aud", tabindex: "-1", "aria-label": TXT.uploadAudio, onchange: () => file.files[0] && sendAudio(file.files[0], file.files[0].name) });
  voiceCtl.append(h("div", { class: "field" }, h("label", { class: "label", for: "voice-loc" }, "Language spoken"), sel), recBtn, h("button", { class: "btn", type: "button", onclick: () => file.click() }, TXT.uploadAudio), file);

  // ---------- safeguards + audit ----------
  const auditHost = h("ul", { class: "audit", "aria-label": "Audit trail" });
  async function loadAudit() {
    try { const m = await api.matter(matterId); clear(auditHost).append(...m.audit.slice().reverse().slice(0, 12).map((a) => h("li", {}, h("span", { class: "mono quiet" }, fmtStamp(a.ts)), h("span", {}, h("b", { style: "font-weight:500" }, a.actor), " ", a.action.replace(/_/g, " "), a.detail?.key ? ` · ${a.detail.key}` : "")))); } catch { /* quiet */ }
  }

  // ---------- compose ----------
  function paintAll() { paintHead(); paintSlots(); paintLedger(); paintBrief(); viewer.set(current.documents); loadAudit(); }
  host.append(head, answer, clockBlock,
    room("papers", TXT.papers, "Add each paper once. Values are read, never assumed.", slotsHost,
      h("div", { class: "desk" }, h("div", { class: "sheet-col" }, viewer.el), h("div", {}, h("h3", { class: "title", style: "margin-bottom:var(--s-3)" }, TXT.ledger), ledgerHost))),
    room("brief", TXT.brief, "A draft for the advocate to check and approve.", briefHost),
    room("ask", TXT.ask, "Questions are answered from this matter's own facts and the deadline engine.", askForm, askOut),
    room("voice", TXT.voice, "A spoken account is transcribed, then masked before any model reads it.", h("div", { class: "voice" }, voiceCtl, voiceOut)),
    room("safeguards", TXT.safeguards, ctx.mode.mode === "live" ? `Model deployment: ${ctx.mode.deployment}` : "Showing a recorded run", h("ul", { class: "six" }, SAFEGUARDS.map(([t, p]) => h("li", {}, h("h3", {}, t), h("p", {}, p)))), h("h3", { class: "label", style: "margin-top:var(--s-6)" }, "Audit trail"), auditHost));
  paintAll(); paintTranscript(current.transcript); paintAnswer(); clock.update(windows, asOf);
  // a date the user is counting from may differ from today; the server's own `today` is authoritative for the first paint
  if (data.today !== ctx.today) { asOf = data.today; clock.update(windows, asOf); }
}

function toast(msg) {
  const t = h("div", { class: "toast", role: "alert" }, msg); document.body.append(t); setTimeout(() => t.remove(), 6000);
}
