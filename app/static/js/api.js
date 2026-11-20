export class ApiError extends Error {
  constructor(message, { retryable = false, status = 0, service = "" } = {}) { super(message); Object.assign(this, { retryable, status, service }); }
}
async function call(path, opts = {}) {
  let res;
  try { res = await fetch(path, opts); }
  catch { throw new ApiError("The desk cannot reach its server. Check that the app is still running, then retry.", { retryable: true }); }
  if (!res.ok) {
    let body = {};
    try { body = await res.json(); } catch { /* not json */ }
    throw new ApiError(body.error || `The server answered ${res.status}.`, { retryable: !!body.retryable, status: res.status, service: body.service || "" });
  }
  return res;
}
const json = async (path, opts) => (await call(path, opts)).json();
const post = (path, body) => json(path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body ?? {}) });
export const api = {
  mode: () => json("/api/mode"),
  locales: () => json("/api/locales"),
  matters: () => json("/api/matters"),
  newMatter: (title) => post("/api/matters", { title }),
  sample: () => post("/api/sample-matter"),
  matter: (id) => json(`/api/matters/${id}`),
  deadlines: (id, today, signal) => json(`/api/matters/${id}/deadlines?today=${today}`, { signal }),
  addDocument: (id, docType, file) => { const f = new FormData(); f.append("doc_type", docType); f.append("file", file); return json(`/api/matters/${id}/documents`, { method: "POST", body: f }); },
  patchFact: (factId, value, actor) => json(`/api/facts/${factId}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ value, actor }) }),
  voice: (id, blob, locale, name) => { const f = new FormData(); f.append("locale", locale); f.append("audio", blob, name || "voice.webm"); return json(`/api/matters/${id}/voice`, { method: "POST", body: f }); },
  brief: (id) => post(`/api/matters/${id}/brief`),
  approve: (id, actor) => post(`/api/matters/${id}/approve`, { actor }),
  ask: (id, question) => post(`/api/matters/${id}/ask`, { question }),
  speak: async (id, locale) => (await call(`/api/matters/${id}/speak`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ locale }) })).blob(),
  fileUrl: (id, docId) => `/api/matters/${id}/documents/${docId}/file`,
};
