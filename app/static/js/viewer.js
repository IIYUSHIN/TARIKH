import { h, svg, clear } from "./dom.js";
import { DOC_LABEL } from "./copy.js";

// The scan viewer: one tab per paper, the image, and an overlay that outlines where a value was read.
export function createViewer({ matterId, fileUrl, onTab }) {
  const tabs = h("div", { class: "tabs", role: "tablist", "aria-label": "Papers" });
  const stage = h("div");
  const cap = h("div", { class: "sheet__cap", "aria-live": "polite" });
  const el = h("div", { class: "sheet", "data-testid": "viewer" }, tabs, stage, cap);
  let docs = [], active = null, poly = [];

  function isPdf(d) { return /\.pdf$/i.test(d.filename); }
  function paintStage() {
    clear(stage);
    const d = docs.find((x) => x.id === active);
    if (!d) { stage.append(h("p", { class: "sheet__empty" }, "No paper yet. Add the cheque to begin.")); cap.textContent = ""; return; }
    if (isPdf(d)) {
      stage.append(h("p", { class: "sheet__empty" }, "This paper is a PDF. ", h("a", { href: fileUrl(matterId, d.id), target: "_blank", rel: "noopener" }, "Open it in a new tab"), " to read it alongside the ledger."));
      return;
    }
    const overlay = svg("svg", { viewBox: "0 0 1 1", preserveAspectRatio: "none", "aria-hidden": "true" });
    for (const p of poly.filter((q) => q.docId === d.id)) {
      const pts = []; for (let i = 0; i + 1 < p.points.length; i += 2) pts.push(`${p.points[i]},${p.points[i + 1]}`);
      const node = svg("polygon", { points: pts.join(" "), class: "on" });
      overlay.append(node);
    }
    stage.append(h("div", { class: "scan" }, h("img", { src: fileUrl(matterId, d.id), alt: `${DOC_LABEL[d.doc_type]}, ${d.filename}` }), overlay));
  }
  function paintTabs() {
    clear(tabs);
    for (const d of docs) {
      tabs.append(h("button", { class: "tab", role: "tab", type: "button", "aria-selected": String(d.id === active), onclick: () => { show(d.id, [], ""); onTab && onTab(d.id); } }, DOC_LABEL[d.doc_type]));
    }
  }
  function set(documents) { docs = documents; if (!docs.some((d) => d.id === active)) active = docs[0]?.id ?? null; paintTabs(); paintStage(); }
  function show(docId, polygons, caption) {
    active = docId; poly = polygons.map((p) => ({ docId, points: p })); paintTabs(); paintStage(); cap.textContent = caption || "";
  }
  return { el, set, show };
}
