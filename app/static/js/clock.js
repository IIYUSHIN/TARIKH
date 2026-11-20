import { h, clear, fmtDate, dayNumber, isoFromDay } from "./dom.js";
import { STATUS_WORD, NEEDS } from "./copy.js";

const PAD = 14;       // days of air either side of the windows
const WORD_CLASS = { open: "st--stamp", closing: "st--stamp", expired: "st--stamp", met: "st--ok" };
// The drawer's 15 days are the other side's clock: the advocate waits through it, so it is never shown as a miss.
const PAY_WORD = { upcoming: "Not yet running", open: "Running", closing: "Ending soon", expired: "Ended" };
const word = (w) => (w.key === "payment" && PAY_WORD[w.status]) || STATUS_WORD[w.status];
const wordClass = (w) => (w.key === "payment" ? (w.status === "met" ? "st--ok" : "") : WORD_CLASS[w.status] || "");
const barClass = (w) => (w.key === "payment" ? ({ open: "wait", closing: "wait", expired: "ended", met: "met" }[w.status] || "upcoming") : (w.status === "unknown" ? "upcoming" : w.status));

function daysText(w, asOf) {
  const a = dayNumber(asOf);
  if (w.status === "unknown") return "needs " + NEEDS[w.key];
  if (w.status === "met") return "";
  if (w.status === "upcoming") { const n = dayNumber(w.opens) - a; return `opens in ${n} day${n === 1 ? "" : "s"}`; }
  if (w.status === "expired") { const n = a - dayNumber(w.closes); return `${w.key === "payment" ? "ended" : "closed"} ${n} day${n === 1 ? "" : "s"} ago`; }
  const n = w.days_left ?? dayNumber(w.closes) - a;
  return n === 0 ? "last day" : `${n} day${n === 1 ? "" : "s"} left`;
}

export function createClock({ onDate, realToday }) {
  let domain = null, asOf = realToday, windows = [];
  const rail = h("div", { class: "clock__axis", style: "height:44px" }, h("div"), h("div", { class: "track" }));
  const axis = h("div", { class: "clock__axis" }, h("div"), h("div", { class: "track" }));
  const rows = h("div");
  const grip = h("div", { class: "today__grip", role: "slider", tabindex: "0", "aria-label": "Day the deadlines are counted from" });
  const line = h("div", { class: "today__line", style: "top:42px" });
  const todayEl = h("div", { class: "today" }, line, grip);
  const layer = h("div", { class: "today-layer", style: "position:absolute;top:0;bottom:0;left:var(--label);right:0;pointer-events:none" }, todayEl);
  grip.style.pointerEvents = "auto";
  const dateInput = h("input", { class: "input", type: "date", id: "asof", "aria-label": "Count deadlines from this date" });
  const todayBtn = h("button", { class: "btn btn--small", type: "button" }, "Today");
  const tableHost = h("details", { class: "clock__table" });
  const plot = h("div", { style: "position:relative" }, rail, axis, rows, layer);
  const root = h("div", { class: "clock", "data-testid": "clock" }, plot,
    h("div", { class: "clock__ctl" },
      h("div", { class: "field" }, h("label", { class: "label", for: "asof" }, "Counting from"), dateInput, todayBtn),
      h("p", { class: "hint" }, "Moving this does not change the matter. It only changes the day the deadlines are counted from.")),
    tableHost);

  const pct = (iso) => ((dayNumber(iso) - domain.d0) / (domain.d1 - domain.d0)) * 100;
  const trackBox = () => axis.querySelector(".track").getBoundingClientRect();

  function setAsOf(iso, live) {
    const n = Math.min(domain.d1, Math.max(domain.d0, dayNumber(iso)));
    asOf = isoFromDay(n);
    paintMarker();
    onDate(asOf, { live });
  }
  function paintMarker() {
    if (!domain) return;
    todayEl.style.left = pct(asOf) + "%";
    grip.textContent = fmtDate(asOf);
    grip.setAttribute("aria-valuemin", domain.d0); grip.setAttribute("aria-valuemax", domain.d1);
    grip.setAttribute("aria-valuenow", dayNumber(asOf)); grip.setAttribute("aria-valuetext", fmtDate(asOf));
    dateInput.value = asOf;
    dateInput.min = isoFromDay(domain.d0); dateInput.max = isoFromDay(domain.d1);
  }
  grip.addEventListener("pointerdown", (e) => {
    grip.setPointerCapture(e.pointerId);
    const move = (ev) => { const b = trackBox(); const f = Math.min(1, Math.max(0, (ev.clientX - b.left) / b.width));
      setAsOf(isoFromDay(Math.round(domain.d0 + f * (domain.d1 - domain.d0))), true); };
    const up = () => { grip.removeEventListener("pointermove", move); grip.removeEventListener("pointerup", up); onDate(asOf, { live: false }); };
    grip.addEventListener("pointermove", move); grip.addEventListener("pointerup", up);
  });
  grip.addEventListener("keydown", (e) => {
    const step = { ArrowLeft: -1, ArrowDown: -1, ArrowRight: 1, ArrowUp: 1, PageDown: -7, PageUp: 7 }[e.key];
    if (!step) return; e.preventDefault(); setAsOf(isoFromDay(dayNumber(asOf) + step), false);
  });
  dateInput.addEventListener("change", () => dateInput.value && setAsOf(dateInput.value, false));
  todayBtn.addEventListener("click", () => setAsOf(realToday, false));

  function update(newWindows, newAsOf) {
    windows = newWindows; asOf = newAsOf;
    const days = windows.flatMap((w) => [w.opens, w.closes]).filter(Boolean).map(dayNumber);
    const base = dayNumber(realToday);
    domain = days.length ? { d0: Math.min(...days) - PAD, d1: Math.max(...days) + PAD } : { d0: base - 30, d1: base + 75 };
    if (dayNumber(asOf) < domain.d0) domain.d0 = dayNumber(asOf) - 3;
    if (dayNumber(asOf) > domain.d1) domain.d1 = dayNumber(asOf) + 3;

    clear(axis.querySelector(".track"));
    const t = axis.querySelector(".track");
    const first = new Date(isoFromDay(domain.d0) + "T00:00:00Z");
    for (let y = first.getUTCFullYear(), m = first.getUTCMonth() + 1; ; m++) {
      if (m > 11) { m = 0; y++; }
      const iso = `${y}-${String(m + 1).padStart(2, "0")}-01`;
      if (dayNumber(iso) > domain.d1) break;
      const label = new Date(iso + "T00:00:00Z").toLocaleString("en-GB", { month: "short", timeZone: "UTC" }) + (m === 0 ? " " + y : "");
      if (pct(iso) < 93) t.append(h("div", { class: "tick-m", style: `left:${pct(iso)}%` }, label));
    }
    clear(rows);
    for (const w of windows) {
      const track = h("div", { class: "track" });
      track.append(...gridlines());
      if (w.opens && w.closes) {
        const l = pct(w.opens), r = pct(w.closes);
        track.append(h("div", { class: `bar-w bar-w--${barClass(w)}`, style: `left:${l}%;width:${Math.max(r - l, 0.4)}%`, "aria-hidden": "true" }));
        const right = r < 82;
        track.append(h("div", { class: "bar-d", style: right ? `left:calc(${r}% + 8px)` : `right:calc(${100 - l}% + 8px)` }, right ? fmtDate(w.closes) : fmtDate(w.opens)));
      } else {
        track.append(h("div", { class: "needs" }, h("span", {}, "Needs " + NEEDS[w.key])));
      }
      const when = w.opens && w.closes ? `${fmtDate(w.opens)} to ${fmtDate(w.closes)}` : "";
      rows.append(h("div", { class: "clock__row", "data-window": w.key, "data-status": w.status },
        h("div", { class: "clock__name" }, h("strong", {}, w.label),
          h("span", {}, h("span", { class: `st ${wordClass(w)}` }, word(w)), daysText(w, asOf) && w.status !== "unknown" ? " · " + daysText(w, asOf) : ""),
          when ? h("span", { class: "mono" }, when) : null),
        track));
    }
    clear(tableHost).append(h("summary", {}, "Show these dates as a table"),
      h("table", {}, h("thead", {}, h("tr", {}, ["Window", "Opens", "Closes", "Status"].map((x) => h("th", { scope: "col" }, x)))),
        h("tbody", {}, windows.map((w) => h("tr", {}, h("th", { scope: "row" }, w.label), h("td", { class: "mono" }, fmtDate(w.opens) || "—"),
          h("td", { class: "mono" }, fmtDate(w.closes) || "—"), h("td", {}, word(w) + (daysText(w, asOf) && w.status !== "unknown" ? ", " + daysText(w, asOf) : "")))))));
    paintMarker();
  }
  function gridlines() {
    const out = [];
    const first = new Date(isoFromDay(domain.d0) + "T00:00:00Z");
    for (let y = first.getUTCFullYear(), m = first.getUTCMonth() + 1; ; m++) {
      if (m > 11) { m = 0; y++; }
      const iso = `${y}-${String(m + 1).padStart(2, "0")}-01`;
      if (dayNumber(iso) > domain.d1) break;
      out.push(h("div", { class: "gridline", style: `left:${pct(iso)}%` }));
    }
    return out;
  }
  return { el: root, update };
}
