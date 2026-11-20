import { h, clear, todayIso } from "./dom.js";
import { api } from "./api.js";
import { MODE } from "./copy.js";
import { renderMatters } from "./matters.js";
import { renderMatter } from "./matter.js";

const ctx = { today: todayIso(), mode: { mode: "live", deployment: "" }, locales: [{ locale: "en-IN", name: "English", available: true }] };
const page = document.getElementById("page");

function paintMode() {
  const host = document.getElementById("mode"); clear(host);
  if (ctx.mode.mode === "replay") host.append(h("b", {}, "Replay"), MODE.replay(ctx.mode.recorded_at));
  else host.hidden = true;
}
async function route() {
  document.title = "Tarikh";
  const m = location.hash.match(/^#\/m\/([\w-]+)/);
  window.scrollTo(0, 0);
  if (m) await renderMatter(page, m[1], ctx); else await renderMatters(page);
  page.focus({ preventScroll: true });
}
async function boot() {
  try { ctx.mode = await api.mode(); if (ctx.mode.today) ctx.today = ctx.mode.today; } catch { /* shown by the first call that fails */ }
  try { ctx.locales = await api.locales(); } catch { /* English only */ }
  paintMode(); window.addEventListener("hashchange", route); route();
}
boot();
