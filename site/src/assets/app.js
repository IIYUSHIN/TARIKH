/* Tarikh demo desk. Renders every app screen from TarikhData; statuses come from TarikhEngine.
   Nothing is saved: changes live in memory until the page is closed. */
(function () {
  'use strict';
  var E = window.TarikhEngine, D = window.TarikhData, T = window.Tarikh, doc = document;
  var app = doc.getElementById('app'); if (!app) return;
  var page = app.getAttribute('data-page'), C = doc.getElementById('content');
  var esc = T.esc, plural = T.plural, dshort = T.dshort, dlong = T.dlong, inr = D.inr, TODAY = D.TODAY;
  D.find = function (id) { for (var i = 0; i < D.MATTERS.length; i++) if (D.MATTERS[i].id === id) return D.MATTERS[i]; return null; };
  function dot(iso) { return iso ? iso.slice(8) + '.' + iso.slice(5, 7) + '.' + iso.slice(0, 4) : ''; }
  function within(iso, a, b) { var k = E.daysBetween(TODAY, iso); return k >= a && k <= b; }
  function toast(msg) { var t = doc.createElement('div'); t.className = 'toast'; t.setAttribute('role', 'status'); t.textContent = msg; doc.body.appendChild(t); setTimeout(function () { t.remove(); }, 2600); }
  function matterLink(m) { return 'matter.html#' + m.id; }
  function refOf(m) { return m.ref || m.id; }

  /* ---------- Server: real accounts and matters. Without a server (a static copy) the desk opens in preview. ---------- */
  var LIVE = false, ME = null;
  function api(path, opts) {
    opts = opts || {}; opts.credentials = 'same-origin';
    if (opts.json !== undefined) { opts.method = opts.method || 'POST'; opts.headers = { 'Content-Type': 'application/json' }; opts.body = JSON.stringify(opts.json); }
    return fetch('../api/' + path, opts).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) {
        if (r.status === 401) { location.href = '../signin.html?next=' + encodeURIComponent('app/' + (location.pathname.split('/').pop() || 'index.html') + location.hash); throw new Error('Sign in to continue.'); }
        if (!r.ok) throw new Error(j.error || 'Something went wrong. Try again.');
        return j;
      });
    });
  }
  function fail(e) { if (e && e.message !== 'Sign in to continue.') toast(e.message); }
  function reload(then) { return api('desk').then(function (j) { D.MATTERS = j.matters; setCounts(); if (then) then(); else render(); }).catch(fail); }
  function setMe(u) {
    var map = { chambers: u ? u.chambers : D.CHAMBERS.name, kind: u ? ({ advocate: 'Tarikh Desk', lender: 'Tarikh Recover', business: 'Tarikh Desk' })[u.kind] : 'Preview, no server', name: u ? u.name : D.CHAMBERS.advocate, email: u ? u.email : 'Sample chambers', initials: (u ? u.name : D.CHAMBERS.advocate).split(/\s+/).filter(function (w) { return /^[A-Za-z]/.test(w) && w !== 'Adv.'; }).map(function (w) { return w[0]; }).slice(0, 2).join('').toUpperCase() };
    app.querySelectorAll('[data-me]').forEach(function (e) { e.textContent = map[e.getAttribute('data-me')]; });
  }
  function boot() {
    fetch('../api/me', { credentials: 'same-origin' }).then(function (r) { if (!r.ok) throw new Error('no server'); return r.json(); }).then(function (j) {
      if (!j.user) { location.href = '../signin.html?next=' + encodeURIComponent('app/' + (location.pathname.split('/').pop() || 'index.html') + location.hash); return; }
      LIVE = true; ME = j.user; TODAY = j.today || TODAY; D.TODAY = TODAY;
      D.CHAMBERS = { name: ME.chambers, advocate: ME.name, city: '' };
      setMe(ME); reload();
    }).catch(function () {
      LIVE = false; setMe(null);
      var f = doc.getElementById('modeflag'); if (f) f.hidden = false;
      C.insertAdjacentHTML('beforebegin', '<div class="preview" style="margin:24px 28px 0"><b>Preview</b><span>This copy has no Tarikh server, so you are seeing sample matters and nothing is saved. Run Tarikh to sign in and keep your own matters.</span></div>');
      setCounts(); render();
    });
  }

  /* ---------- Sidebar: a rail that folds, with a sliding marker ---------- */
  (function () {
    var nav = app.querySelector('.side nav'), pill = nav && nav.querySelector('.pill'), cur = nav && nav.querySelector('[aria-current=page]');
    function place(el) { if (!pill) return; if (!el) { pill.style.opacity = '0'; return; } pill.style.opacity = '1'; pill.style.transform = 'translateY(' + el.offsetTop + 'px)'; }
    place(cur);
    if (nav) nav.querySelectorAll('a.it').forEach(function (a) { a.addEventListener('mouseenter', function () { place(a); }); a.addEventListener('focus', function () { place(a); }); });
    if (nav) nav.addEventListener('mouseleave', function () { place(cur); });
    var col = app.querySelector('.collapse');
    try { if (localStorage.getItem('tarikh.rail') === '1') { app.classList.add('rail'); col.setAttribute('aria-pressed', 'true'); } } catch (e) {}
    if (col) col.addEventListener('click', function () { var on = app.classList.toggle('rail'); col.setAttribute('aria-pressed', String(on)); col.setAttribute('aria-label', on ? 'Expand the sidebar' : 'Collapse the sidebar'); try { localStorage.setItem('tarikh.rail', on ? '1' : '0'); } catch (e) {} setTimeout(function () { place(cur); }, 460); });
    var so = doc.getElementById('signout');
    if (so) so.addEventListener('click', function () { if (!LIVE) { location.href = '../index.html'; return; } fetch('../api/auth/signout', { method: 'POST', credentials: 'same-origin' }).then(function () { location.href = '../signin.html'; }); });
  })();
  function ranked() { return D.MATTERS.map(function (m) { return { m: m, s: T.statusOf(m) }; }).sort(function (a, b) { return a.s.rank - b.s.rank; }); }
  function draftsWaiting() { var n = []; D.MATTERS.forEach(function (m) { (m.drafts || []).forEach(function (d) { if (d.s === 'Awaiting approval') n.push({ m: m, d: d }); }); }); return n; }

  /* ---------- Shell: menu, counts, command palette ---------- */
  var mb = app.querySelector('.app-menu');
  mb.addEventListener('click', function () { var o = app.classList.toggle('nav-open'); mb.setAttribute('aria-expanded', String(o)); });
  app.addEventListener('click', function (e) { if (app.classList.contains('nav-open') && !e.target.closest('.side') && !e.target.closest('.app-menu')) { app.classList.remove('nav-open'); mb.setAttribute('aria-expanded', 'false'); } });
  function setCounts() {
    var r = ranked();
    var c = { today: r.filter(function (x) { return x.s.cls === 'hot' || x.s.cls === 'warn'; }).length, matters: D.MATTERS.length, drafts: draftsWaiting().length, diary: '' };
    app.querySelectorAll('[data-count-for]').forEach(function (e) { e.textContent = c[e.getAttribute('data-count-for')] || ''; });
  }
  var pal = doc.getElementById('palette'), pq = doc.getElementById('palette-q'), pl = doc.getElementById('palette-list'), psel = 0;
  var PAGES = [['Today', 'index.html'], ['Matters', 'matters.html'], ['Diary', 'diary.html'], ['Drafts', 'drafts.html'], ['Portfolio (Recover)', 'portfolio.html'], ['Check a cheque', '../check.html'], ['Rule register', '../law.html']];
  function palRender() {
    var q = pq.value.trim().toLowerCase(), h = '', items = [];
    var ms = D.MATTERS.filter(function (m) { return !q || (refOf(m) + ' ' + m.accused + ' ' + m.complainant + ' ' + (m.caseNo || '') + ' ' + m.court).toLowerCase().indexOf(q) >= 0; }).slice(0, 7);
    var ps = PAGES.filter(function (p) { return !q || p[0].toLowerCase().indexOf(q) >= 0; });
    if (ms.length) { h += '<li class="ph">Matters</li>'; ms.forEach(function (m) { items.push(matterLink(m)); h += '<li><a role="option" href="' + matterLink(m) + '"><b>' + esc(m.accused) + '</b><span>' + esc(refOf(m)) + ' · ' + esc(T.statusOf(m).text) + '</span></a></li>'; }); }
    if (ps.length) { h += '<li class="ph">Go to</li>'; ps.forEach(function (p) { items.push(p[1]); h += '<li><a role="option" href="' + p[1] + '"><b>' + p[0] + '</b><span>Page</span></a></li>'; }); }
    if (!items.length) h = '<li class="ph">Nothing matches “' + esc(q) + '”</li>';
    pl.innerHTML = h; psel = 0; mark();
  }
  function mark() { var as = pl.querySelectorAll('a'); as.forEach(function (a, i) { a.setAttribute('aria-selected', String(i === psel)); }); }
  function openPal() { if (pal.showModal) { pal.showModal(); pq.value = ''; palRender(); pq.focus(); } }
  doc.getElementById('open-palette').addEventListener('click', openPal);
  doc.addEventListener('keydown', function (e) { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openPal(); } });
  pq.addEventListener('input', palRender);
  pq.addEventListener('keydown', function (e) {
    var as = pl.querySelectorAll('a');
    if (e.key === 'ArrowDown') { e.preventDefault(); psel = Math.min(as.length - 1, psel + 1); mark(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); psel = Math.max(0, psel - 1); mark(); }
    else if (e.key === 'Enter' && as[psel]) { e.preventDefault(); location.href = as[psel].getAttribute('href'); pal.close(); }
  });
  pal.addEventListener('click', function (e) { if (e.target === pal) pal.close(); var a = e.target.closest('a'); if (a) { pal.close(); } });

  /* ---------- New matter ---------- */
  function newMatter() {
    var dlg = doc.getElementById('nmd');
    if (!dlg) {
      doc.body.insertAdjacentHTML('beforeend', '<dialog class="modal" id="nmd" aria-labelledby="nmt"><form id="nmf" novalidate><div class="panel-h"><h2 id="nmt">Open a matter</h2><button class="btn sm" type="button" data-close>Cancel</button></div><div class="panel-b stack">' +
        '<p class="small">Enter what you know now. You can add the papers on the next screen and Tarikh will read them.</p>' +
        '<div class="grid-2" style="grid-template-columns:1fr 1fr"><div class="field"><label for="nm-c">Complainant (your client)</label><input class="inp" id="nm-c" required></div><div class="field"><label for="nm-a">Accused (who drew the cheque)</label><input class="inp" id="nm-a" required></div>' +
        '<div class="field"><label for="nm-amt">Cheque amount (₹)</label><input class="inp" id="nm-amt" inputmode="numeric"></div><div class="field"><label for="nm-no">Cheque number</label><input class="inp" id="nm-no"></div></div>' +
        '<div class="field"><label for="nm-court">Court</label><input class="inp" id="nm-court" placeholder="Judicial Magistrate First Class, Chandigarh"></div>' +
        '<div class="grid-2" style="grid-template-columns:1fr 1fr">' + [['cheque_date', 'Date on the cheque'], ['memo_received_on', 'Return memo reached the client'], ['notice_sent_on', 'Notice sent'], ['notice_delivered_on', 'Drawer received the notice']].map(function (f) { return '<div class="field"><label for="nm-' + f[0] + '">' + f[1] + '</label><input class="inp" type="date" id="nm-' + f[0] + '"></div>'; }).join('') + '</div>' +
        '<p class="err" id="nm-err" role="alert" style="color:var(--red);font-weight:650;font-size:13px"></p><div class="acts"><button class="btn red" type="submit">Open matter</button></div></div></form></dialog>');
      dlg = doc.getElementById('nmd');
      dlg.querySelector('[data-close]').addEventListener('click', function () { dlg.close(); });
      doc.getElementById('nmf').addEventListener('submit', function (e) {
        e.preventDefault();
        var c = doc.getElementById('nm-c').value.trim(), a = doc.getElementById('nm-a').value.trim(), err = doc.getElementById('nm-err');
        if (!c || !a) { err.textContent = 'Enter both parties.'; (c ? doc.getElementById('nm-a') : doc.getElementById('nm-c')).focus(); return; }
        var entries = {}; ['cheque_date', 'memo_received_on', 'notice_sent_on', 'notice_delivered_on'].forEach(function (k) { var v = doc.getElementById('nm-' + k).value; if (v) entries[k] = v; });
        var body = { complainant: c, accused: a, amount: doc.getElementById('nm-amt').value.replace(/[^0-9]/g, ''), chequeNo: doc.getElementById('nm-no').value.trim(), court: doc.getElementById('nm-court').value.trim(), entries: entries };
        if (!LIVE) { err.textContent = 'Opening matters needs the Tarikh server. This preview cannot save.'; return; }
        api('matters', { json: body }).then(function (m) { dlg.close(); location.href = 'matter.html#' + m.id; }).catch(function (e2) { err.textContent = e2.message; });
      });
    }
    dlg.showModal(); doc.getElementById('nm-c').focus();
  }
  doc.addEventListener('click', function (e) { if (e.target.closest('[data-new]')) newMatter(); });
  function emptyDesk() {
    return '<div class="empty"><p class="kicker">Your desk is empty</p><h2 class="h-m">Open your first matter.</h2><p class="small" style="max-width:560px">Add the parties and the dates you know, then upload the cheque, the return memo and the notice. Or load thirteen fictional matters at every stage to see each screen working.</p><div class="acts"><button class="btn red" data-new>Open a matter</button><button class="btn" id="load-samples">Load sample matters</button></div></div>';
  }
  doc.addEventListener('click', function (e) {
    var b = e.target.closest('#load-samples'); if (!b) return;
    b.disabled = true; b.innerHTML = '<span class="spin"></span> Loading';
    api('desk/samples', { json: {} }).then(function (r) { toast(plural(r.created, 'sample matter', 'sample matters') + ' added to your desk.'); reload(); }).catch(fail);
  });

  /* ---------- Today ---------- */
  function today() {
    if (!D.MATTERS.length) { C.innerHTML = '<h1>Good morning, ' + esc((D.CHAMBERS.advocate || '').split(' ')[0]) + '.</h1><p class="sub">' + dlong(TODAY) + ' · ' + esc(D.CHAMBERS.name) + '</p><div style="margin-top:24px">' + emptyDesk() + '</div>'; return; }
    var r = ranked(), pre = r.filter(function (x) { return !x.m.filed && x.m.stage !== 'settled' && x.s.cls !== 'gone'; });
    var hear = D.MATTERS.filter(function (m) { return m.next && within(m.next[0], 0, 21); }).sort(function (a, b) { return a.next[0] < b.next[0] ? -1 : 1; });
    var waits = draftsWaiting(), missing = D.MATTERS.filter(function (m) { return !m.memo || (m.sent && !m.delivered); });
    var gone = r.filter(function (x) { return !x.m.filed && x.s.cls === 'gone'; });
    var hot = pre.filter(function (x) { return x.s.cls === 'hot'; });
    C.innerHTML =
      '<div class="mhead"><div><h1>Good morning' + (LIVE ? ', ' + esc(ME.name.split(' ')[0]) : '') + '. ' + (hot.length ? plural(hot.length, 'deadline needs', 'deadlines need') + ' you this week.' : 'Nothing is closing this week.') + '</h1><p class="sub">' + T.WD[T.dow(TODAY)] + ', ' + dlong(TODAY) + ' · ' + esc(D.CHAMBERS.name) + '</p></div>' +
      '<div style="--lw:118px">' + T.leafHTML(TODAY, 'Today', '') + '</div></div>' +
      '<div class="kpis" style="margin-top:20px">' +
      '<a class="kpi hot" href="matters.html"><div class="k">Closing in 7 days</div><div class="v">' + hot.length + '</div><div class="s">complaint or notice deadlines</div></a>' +
      '<a class="kpi" href="diary.html"><div class="k">Hearings, next 7 days</div><div class="v">' + hear.filter(function (m) { return within(m.next[0], 0, 7); }).length + '</div><div class="s">across ' + plural(new Set(hear.map(function (m) { return m.court; })).size, 'court', 'courts') + '</div></a>' +
      '<a class="kpi" href="drafts.html"><div class="k">Drafts to approve</div><div class="v">' + waits.length + '</div><div class="s">only an advocate can approve</div></a>' +
      '<a class="kpi" href="#missing"><div class="k">Dates to enter</div><div class="v">' + missing.length + '</div><div class="s">on no paper, so asked</div></a></div>' +
      '<div class="grid-2" style="margin-top:16px"><div class="stack">' +
      '<section class="panel"><div class="panel-h"><h2>Deadlines, most urgent first</h2><span>counted by rule</span></div>' +
      '<table class="dtable"><tbody>' + pre.map(function (x) { return '<tr data-href="' + matterLink(x.m) + '"><td><b>' + esc(x.m.accused) + '</b><span class="s">' + esc(refOf(x.m)) + ' · ' + esc(x.m.complainant) + '</span></td><td class="hide-sm">' + (x.s.key ? '<b>' + dshort(x.s.key) + '</b><span class="s">' + esc(x.s.keyLabel) + '</span>' : '<span class="s">' + esc(x.s.keyLabel) + '</span>') + '</td><td class="r">' + T.chip(x.s) + '</td></tr>'; }).join('') + '</tbody></table></section>' +
      (gone.length ? '<section class="panel"><div class="panel-h"><h2>Windows that have closed</h2><span>for the advocate to review</span></div><table class="dtable"><tbody>' + gone.map(function (x) { return '<tr data-href="' + matterLink(x.m) + '"><td><b>' + esc(x.m.accused) + '</b><span class="s">' + esc(x.m.complainant) + ' · ' + inr(x.m.amount) + '</span></td><td class="r">' + T.chip(x.s) + '</td></tr>'; }).join('') + '</tbody></table></section>' : '') +
      '</div><div class="stack">' +
      '<section class="panel"><div class="panel-h"><h2>Hearings, next three weeks</h2><a class="tlink" href="diary.html" style="font-size:13px">Diary</a></div><div class="panel-b"><ol class="tl">' + hear.map(function (m, i) { return '<li class="' + (i === 0 ? 'next' : '') + '"><span class="d">' + T.WD[T.dow(m.next[0])].slice(0, 3) + ' ' + dshort(m.next[0]) + '</span><b><a href="' + matterLink(m) + '" style="text-decoration:none">' + esc(m.accused) + '</a></b><span class="o">' + esc(m.next[1]) + ' · ' + esc(m.court.replace('Judicial Magistrate First Class, ', 'JMIC ')) + '</span></li>'; }).join('') + '</ol></div></section>' +
      '<section class="panel" id="missing"><div class="panel-h"><h2>Dates no paper shows</h2><span>enter to start the clocks</span></div><div class="panel-b stack">' + missing.map(function (m) { return '<div><b>' + esc(m.accused) + '</b><p class="small">' + esc(!m.memo ? 'When did the return memo reach ' + m.complainant + '?' : 'When did the drawer receive the notice?') + '</p><a class="btn sm" style="margin-top:8px" href="' + matterLink(m) + '">Enter the date</a></div>'; }).join('') + '</div></section>' +
      '<section class="panel"><div class="panel-h"><h2>Waiting for your approval</h2></div><div class="panel-b stack">' + waits.map(function (w) { return '<div style="display:flex;justify-content:space-between;gap:10px;align-items:center"><div><b>' + esc(w.d.t) + '</b><p class="small">' + esc(w.m.accused) + '</p></div><a class="btn sm" href="drafts.html#' + w.m.id + '">Review</a></div>'; }).join('') + '</div></section>' +
      '</div></div>';
  }

  /* ---------- Matters ---------- */
  var mFilter = 'all', mQuery = '';
  function matters() {
    var groups = { all: function () { return true; }, pre: function (m) { return !m.filed && m.stage !== 'settled'; }, court: function (m) { return m.filed && m.stage !== 'settled' && m.stage !== 'decided'; }, closed: function (m) { return m.stage === 'settled' || m.stage === 'decided'; } };
    var names = [['all', 'All'], ['pre', 'Before filing'], ['court', 'In court'], ['closed', 'Closed']];
    var rows = ranked().filter(function (x) { return groups[mFilter](x.m) && (!mQuery || (x.m.id + ' ' + x.m.accused + ' ' + x.m.complainant + ' ' + x.m.court).toLowerCase().indexOf(mQuery) >= 0); });
    if (!D.MATTERS.length) { C.innerHTML = '<h1>Matters</h1><div style="margin-top:24px">' + emptyDesk() + '</div>'; return; }
    C.innerHTML = '<div class="mhead"><div><h1>Matters</h1><p class="sub">Ordered by what runs out first. Click a matter to open it.</p></div><div class="acts"><button class="btn red sm" data-new>Open a matter</button></div></div>' +
      '<div class="filters" style="margin:22px 0 14px">' + names.map(function (n) { return '<button class="fbtn" data-f="' + n[0] + '" aria-pressed="' + (mFilter === n[0]) + '">' + n[1] + '<em>' + D.MATTERS.filter(groups[n[0]]).length + '</em></button>'; }).join('') +
      '<span style="flex:1"></span><label class="sr" for="mq">Filter matters</label><input class="inp sm" id="mq" placeholder="Filter by party or court" value="' + esc(mQuery) + '"></div>' +
      '<section class="panel"><table class="dtable"><thead><tr><th scope="col">Matter</th><th scope="col" class="hide-sm">Court</th><th scope="col" class="r hide-sm">Amount</th><th scope="col" class="hide-sm">Key date</th><th scope="col" class="r">Status</th></tr></thead><tbody>' +
      (rows.length ? rows.map(function (x) { var m = x.m; return '<tr data-href="' + matterLink(m) + '"><td><b>' + esc(m.accused) + '</b><span class="s">' + esc(refOf(m)) + ' · ' + esc(m.complainant) + (m.caseNo ? ' · ' + m.caseNo : '') + '</span></td><td class="hide-sm">' + esc(m.court.replace('Judicial Magistrate First Class, ', 'JMIC, ')) + '</td><td class="r hide-sm">' + inr(m.amount) + '</td><td class="hide-sm">' + (x.s.key ? '<b>' + dshort(x.s.key) + '</b><span class="s">' + esc(x.s.keyLabel) + '</span>' : '<span class="s">' + esc(x.s.keyLabel) + '</span>') + '</td><td class="r">' + T.chip(x.s) + '</td></tr>'; }).join('') : '<tr><td colspan="5"><p class="small">No matters match. Clear the filter to see all ' + D.MATTERS.length + '.</p></td></tr>') +
      '</tbody></table></section>';
    C.querySelectorAll('.fbtn').forEach(function (b) { b.addEventListener('click', function () { mFilter = b.getAttribute('data-f'); matters(); }); });
    var q = doc.getElementById('mq'); q.addEventListener('input', function () { mQuery = q.value.trim().toLowerCase(); var pos = q.selectionStart; matters(); var n = doc.getElementById('mq'); n.focus(); n.setSelectionRange(pos, pos); });
  }

  /* ---------- One matter ---------- */
  var mTab = 'clocks';
  function activity(m) {
    var a = (m.log || []).slice();
    (m.drafts || []).forEach(function (d) { if (d.s !== 'Not started') a.push([d.s === 'Approved' ? 'Approved: ' + d.t : 'Drafted: ' + d.t, d.s === 'Approved' ? D.CHAMBERS.advocate : 'Tarikh, for review']); });
    if (m.delivered) a.push(['Notice delivery date entered', 'Clerk · from postal tracking']);
    if (m.memo) a.push(['Return memo read', 'Reason: ' + m.reason.toLowerCase()]);
    a.push(['Cheque read', 'Cheque ' + m.chequeNo + ' · ' + inr(m.amount)]);
    a.push(['Matter opened', m.id]);
    return a;
  }
  function matter() {
    var id = (location.hash || '').slice(1), m = D.find(id) || (LIVE ? null : D.MATTERS[0]);
    if (!m) { C.innerHTML = D.MATTERS.length ? '<h1>Matter not found</h1><p class="sub">It may belong to another account. <a href="matters.html">Back to matters</a></p>' : emptyDesk(); return; }
    if (LIVE && !m.log) { api('desk/' + m.id).then(function (v) { D.MATTERS[D.MATTERS.indexOf(m)] = v; matter(); }).catch(fail); C.innerHTML = '<p class="sub"><span class="spin"></span> Opening the matter</p>'; return; }
    renderMatter(m);
  }
  function save(promise, msg) { return promise.then(function (v) { var i = D.MATTERS.findIndex(function (x) { return x.id === v.id; }); if (i >= 0) D.MATTERS[i] = v; setCounts(); if (msg) toast(msg); renderMatter(v); }).catch(fail); }
  function renderMatter(m) {
    var s = T.statusOf(m), w = s.windows;
    doc.title = m.accused + ' · Tarikh';
    var leafDate = m.next ? m.next[0] : s.key, leafLabel = m.next ? 'Next hearing' : s.keyLabel;
    var tabs = [['clocks', 'Clocks'], ['papers', 'Papers and facts'], ['hearings', 'Hearings'], ['drafts', 'Drafts'], ['brief', 'AI brief'], ['ask', 'Ask the file'], ['settle', 'Settlement'], ['activity', 'Activity']];
    C.innerHTML = '<div class="mhead"><div><p class="tiny" style="font-family:var(--mono)"><a href="matters.html">Matters</a> / ' + esc(refOf(m)) + (m.sample ? ' · sample' : '') + '</p><h1 style="margin-top:8px">' + esc(m.complainant) + ' <span style="color:var(--g400)">v.</span> ' + esc(m.accused) + '</h1>' +
      '<div class="meta">' + (m.chequeNo ? '<span>Cheque <b>' + esc(m.chequeNo) + '</b></span>' : '') + '<span>Amount <b>' + (m.amount ? inr(m.amount) : 'not entered') + '</b></span><span>' + esc(m.court) + '</span>' + (m.caseNo ? '<span>Case <b>' + esc(m.caseNo) + '</b></span>' : '') + '<span>' + T.chip(s) + '</span></div></div>' +
      (leafDate ? '<div style="--lw:140px">' + T.leafHTML(leafDate, leafLabel.length > 22 ? leafLabel.slice(0, 22) + '…' : leafLabel, '') + '</div>' : '') + '</div>' +
      '<div class="tabs" role="tablist" style="margin-top:24px">' + tabs.map(function (t) { return '<button role="tab" data-t="' + t[0] + '" aria-selected="' + (mTab === t[0]) + '">' + t[1] + '</button>'; }).join('') + '</div>' +
      '<div id="mt" style="margin-top:18px"></div>';
    C.querySelectorAll('.tabs button').forEach(function (b) { b.addEventListener('click', function () { mTab = b.getAttribute('data-t'); renderMatter(m); }); });
    var P = doc.getElementById('mt');
    function dateInputs(keys) { return keys.map(function (f) { return '<div class="field"><label for="f-' + f[0] + '">' + f[1] + '</label><input class="inp" type="date" id="f-' + f[0] + '" value="' + (m[f[2]] || '') + '"></div>'; }).join(''); }
    var DATE_FIELDS = [['cheque_date', 'Date on the cheque', 'cheque'], ['presented_on', 'Presented to the bank', 'presented'], ['memo_received_on', 'Return memo reached the client', 'memo'], ['notice_sent_on', 'Demand notice sent', 'sent'], ['notice_delivered_on', 'Drawer received the notice', 'delivered']];
    if (mTab === 'clocks') {
      var needs = !m.memo || !m.sent || !m.delivered;
      P.innerHTML = (m.filed ? '<section class="panel"><div class="panel-b"><p class="kicker">Filed</p><p class="h-m" style="margin-top:12px">Filed on ' + dlong(m.filed) + (w.complaint.closes ? (E.daysBetween(m.filed, w.complaint.closes) >= 0 ? ', inside the window.' : ', after the window closed.') : '.') + '</p>' + (w.complaint.opens ? '<p class="small" style="margin-top:8px">The complaint window ran from ' + dlong(w.complaint.opens) + ' to ' + dlong(w.complaint.closes) + '.</p>' : '') + '</div></section>' : '') +
        (m.cheque && m.memo && m.sent && m.delivered ? '<section class="panel" style="margin-top:16px"><div class="panel-b" id="ltbox"></div></section>' : '') +
        '<section class="panel" style="margin-top:16px"><div class="panel-h"><h2>' + (needs ? 'Dates the clocks still need' : 'The five dates') + '</h2><span>entered dates are marked as entries, never as paper</span></div><div class="panel-b"><form id="dates" class="stack" style="max-width:640px"><div class="grid-2" style="grid-template-columns:1fr 1fr">' + dateInputs(DATE_FIELDS) + '</div><div class="acts"><button class="btn solid" type="submit">Save and count</button></div></form>' +
        (!m.cheque && !m.memo ? '<p class="small" style="margin-top:14px">No dates yet. Enter them here, or upload the papers under Papers and facts.</p>' : (!m.sent && w.notice.closes ? '<p class="h-s" style="margin-top:18px">Notice must go by ' + dlong(w.notice.closes) + '.</p>' : '')) + '</div></section>';
      doc.getElementById('dates').addEventListener('submit', function (e) {
        e.preventDefault(); var entries = {}; DATE_FIELDS.forEach(function (f) { entries[f[0]] = doc.getElementById('f-' + f[0]).value || null; });
        if (!LIVE) { DATE_FIELDS.forEach(function (f) { m[f[2]] = entries[f[0]]; }); toast('Preview only: counted, not saved.'); renderMatter(m); return; }
        save(api('desk/' + m.id, { method: 'PATCH', json: { entries: entries } }), 'Dates saved. Clocks recounted.');
      });
      var box = doc.getElementById('ltbox');
      if (box) { var lt = doc.createElement('div'); ['cheque', 'presented', 'memo', 'sent', 'delivered'].forEach(function (k) { if (m[k]) lt.setAttribute('data-' + k, m[k]); }); if (!m.presented) lt.setAttribute('data-presented', m.cheque); lt.setAttribute('data-today', m.filed ? m.filed : TODAY); lt.setAttribute('data-heading', 'Move the dates'); lt.setAttribute('data-sub', 'What-if only. Moving a pin changes nothing that is saved.'); box.appendChild(lt); T.mountLongTable(lt); }
    } else if (mTab === 'papers') {
      var papers = m.papers || [];
      var TYPES = [['cheque', 'Cheque'], ['return_memo', 'Return memo'], ['demand_notice', 'Demand notice']];
      P.innerHTML = '<div class="grid-2"><div class="stack">' + TYPES.map(function (t) {
        var d = papers.filter(function (x) { return x.type === t[0]; })[0];
        return '<section class="panel"><div class="panel-h"><h2>' + t[1] + '</h2><span>' + (d ? 'read by Azure' : 'not added') + '</span></div><div class="panel-b">' +
          (d ? '<table class="fields"><tbody>' + d.facts.map(function (f) { return '<tr><td>' + esc(f.label) + '</td><td class="v">' + (f.manual ? '<input class="inp sm" type="date" data-fact="' + f.id + '" value="' + (f.value || '') + '" aria-label="' + esc(f.label) + '">' : (f.value ? esc(f.value) : '<span class="chip warn plain">not read</span>')) + (f.flag ? '<span class="s" style="display:block;font-weight:400;font-size:12px;color:var(--amber)">' + esc(f.flag) + '</span>' : '') + '</td><td class="s">' + (f.confidence != null ? '<span class="conf">' + Math.round(f.confidence * 100) + '%</span>' : (f.manual ? '<span class="chip warn plain">entry</span>' : '')) + '</td></tr>'; }).join('') + '</tbody></table>' +
            (d.observations && d.observations.length ? '<p class="small" style="margin-top:12px">Seen on the cheque: ' + d.observations.map(function (o) { return esc(o.label) + ' ' + o.status; }).join(' · ') + '</p>' : '') + '<p style="margin-top:12px"><a class="tlink" href="..' + d.url + '" target="_blank" rel="noopener">Open the paper</a></p>'
            : '<form class="drop" data-up="' + t[0] + '"><label class="small" for="up-' + t[0] + '">Photo or scan (PNG, JPEG, PDF, up to 15 MB)</label><input id="up-' + t[0] + '" type="file" accept="image/png,image/jpeg,application/pdf,image/tiff"><button class="btn sm solid" type="submit">Upload and read</button></form>') + '</div></section>';
      }).join('') + '</div><section class="panel"><div class="panel-h"><h2>Client’s account</h2><span>Azure Speech, then personal details masked</span></div><div class="panel-b">' +
        (m.transcript ? '<p>' + esc(m.transcript.redacted_text) + '</p>' : '<form class="drop" id="voice"><label class="small" for="vc">Recording of the client (WAV or MP3)</label><input id="vc" type="file" accept="audio/*"><label class="small" for="vl">Language</label><select class="sel sm" id="vl"><option value="en-IN">English</option><option value="hi-IN">Hindi</option><option value="pa-IN">Punjabi</option></select><button class="btn sm solid" type="submit">Transcribe and mask</button></form>') + '</div></section></div>';
      P.querySelectorAll('form[data-up]').forEach(function (f) {
        f.addEventListener('submit', function (e) {
          e.preventDefault(); var file = f.querySelector('input').files[0];
          if (!file) { toast('Choose a file first.'); return; }
          if (!LIVE) { toast('Reading papers needs the Tarikh server and Azure.'); return; }
          var fd = new FormData(); fd.append('doc_type', f.getAttribute('data-up')); fd.append('file', file);
          f.classList.add('busy'); f.querySelector('button').innerHTML = '<span class="spin"></span> Azure is reading';
          api('matters/' + m.id + '/documents', { method: 'POST', body: fd }).then(function (r) { (r.warnings || []).forEach(toast); return api('desk/' + m.id); }).then(function (v) { D.MATTERS[D.MATTERS.findIndex(function (x) { return x.id === v.id; })] = v; toast('Read. Check each value against the paper.'); renderMatter(v); }).catch(function (e2) { f.classList.remove('busy'); f.querySelector('button').textContent = 'Upload and read'; fail(e2); });
        });
      });
      P.querySelectorAll('input[data-fact]').forEach(function (inp) { inp.addEventListener('change', function () { if (!LIVE) return; api('facts/' + inp.getAttribute('data-fact'), { method: 'PATCH', json: { value: inp.value || null } }).then(function () { return api('desk/' + m.id); }).then(function (v) { D.MATTERS[D.MATTERS.findIndex(function (x) { return x.id === v.id; })] = v; toast('Saved. Clocks recounted.'); renderMatter(v); }).catch(fail); }); });
      var vf = doc.getElementById('voice');
      if (vf) vf.addEventListener('submit', function (e) { e.preventDefault(); var file = doc.getElementById('vc').files[0]; if (!file) { toast('Choose a recording first.'); return; } if (!LIVE) { toast('Needs the Tarikh server and Azure.'); return; } var fd = new FormData(); fd.append('locale', doc.getElementById('vl').value); fd.append('audio', file); vf.classList.add('busy'); api('matters/' + m.id + '/voice', { method: 'POST', body: fd }).then(function () { return api('desk/' + m.id); }).then(function (v) { D.MATTERS[D.MATTERS.findIndex(function (x) { return x.id === v.id; })] = v; renderMatter(v); }).catch(function (e2) { vf.classList.remove('busy'); fail(e2); }); });
    } else if (mTab === 'hearings') {
      var hs = (m.hearings || []);
      P.innerHTML = '<div class="grid-2"><section class="panel"><div class="panel-h"><h2>Hearings</h2><span>' + plural(hs.filter(function (h) { return /Adjourned|Not served/.test(h[2]); }).length, 'adjournment', 'adjournments') + ' so far</span></div><div class="panel-b">' +
        (hs.length || m.next ? '<ol class="tl">' + hs.map(function (h) { return '<li class="' + (/Adjourned|Not served/.test(h[2]) ? 'adj' : '') + '"><span class="d">' + dlong(h[0]) + '</span><b>' + esc(h[1]) + '</b><span class="o">' + esc(h[2]) + '</span></li>'; }).join('') + (m.next ? '<li class="next"><span class="d">' + dlong(m.next[0]) + ' · next</span><b>' + esc(m.next[1]) + '</b><span class="o">' + (E.daysBetween(TODAY, m.next[0]) >= 0 ? 'In ' + plural(E.daysBetween(TODAY, m.next[0]), 'day', 'days') : 'Date has passed: record what happened') + '</span></li>' : '') + '</ol>' : '<p class="small">No hearings recorded yet.</p>') + '</div></section>' +
        '<section class="panel"><div class="panel-h"><h2>Record a hearing</h2><span>and fix the next date</span></div><div class="panel-b"><form id="hf" class="stack" style="gap:12px">' +
        '<div class="field"><label for="h-d">Date of hearing</label><input class="inp" type="date" id="h-d" value="' + (m.next && E.daysBetween(m.next[0], TODAY) >= 0 ? m.next[0] : TODAY) + '"></div>' +
        '<div class="field"><label for="h-p">What it was for</label><input class="inp" id="h-p" value="' + esc(m.next ? m.next[1] : '') + '" placeholder="Appearance of accused"></div>' +
        '<div class="field"><label for="h-o">What happened</label><select class="sel" id="h-o"><option>Done</option><option>Adjourned: accused absent</option><option>Adjourned: counsel unavailable</option><option>Adjourned: court on leave</option><option>Not served</option><option>Part heard</option><option>Settled in court</option></select></div>' +
        '<div class="grid-2" style="grid-template-columns:1fr 1fr"><div class="field"><label for="h-nd">Next date</label><input class="inp" type="date" id="h-nd"></div><div class="field"><label for="h-np">Next date is for</label><input class="inp" id="h-np" placeholder="Complainant evidence"></div></div>' +
        '<div class="acts"><button class="btn red" type="submit">Save hearing</button></div></form></div></section></div>';
      doc.getElementById('hf').addEventListener('submit', function (e) {
        e.preventDefault(); var body = { date: doc.getElementById('h-d').value, purpose: doc.getElementById('h-p').value, outcome: doc.getElementById('h-o').value, next_date: doc.getElementById('h-nd').value || null, next_purpose: doc.getElementById('h-np').value };
        if (!body.date || !body.purpose.trim()) { toast('Enter the date and what the hearing was for.'); return; }
        if (!LIVE) { m.hearings = (m.hearings || []).concat([[body.date, body.purpose, body.outcome]]); m.next = body.next_date ? [body.next_date, body.next_purpose || 'Next hearing'] : null; toast('Preview only: not saved.'); renderMatter(m); return; }
        save(api('desk/' + m.id + '/hearings', { json: body }), 'Hearing saved.');
      });
    } else if (mTab === 'drafts') {
      var ds = m.drafts || [];
      P.innerHTML = '<section class="panel"><div class="panel-h"><h2>Drafts</h2><a class="btn sm" href="drafts.html#' + m.id + '">Open the drafting desk</a></div><table class="dtable"><tbody>' + (ds.length ? ds.map(function (d) { return '<tr data-href="drafts.html#' + m.id + '"><td><b>' + esc(d.t) + '</b>' + (d.by ? '<span class="s">Approved by ' + esc(d.by) + '</span>' : '') + '</td><td class="r"><span class="chip ' + (d.s === 'Approved' ? 'ok' : d.s === 'Awaiting approval' ? 'warn' : '') + '">' + esc(d.s) + '</span></td></tr>'; }).join('') : '<tr><td><p class="small">No drafts yet. Seven documents are built from this matter’s facts in the drafting desk.</p></td></tr>') + '</tbody></table></section>';
    } else if (mTab === 'brief') {
      var br = m.brief;
      P.innerHTML = '<section class="panel"><div class="panel-h"><h2>AI brief</h2><span>Foundry model; a sentence survives only if it cites a fact</span></div><div class="panel-b">' +
        (br ? '<div>' + br.claims.map(function (c, i) { return '<div class="claim"><span class="n">' + (i + 1) + '</span><div>' + esc(c.text) + '<span class="s" style="display:block;font-size:12px;color:var(--g600);margin-top:4px">Sources: ' + c.fact_ids.map(esc).join(', ') + '</span></div></div>'; }).join('') + '</div>' + (br.flagged.length ? '<p class="small" style="margin-top:14px">Removed before you saw it: ' + br.flagged.map(esc).join(' · ') + '</p>' : '') + '<p class="small" style="margin-top:14px">' + (m.approved_by ? 'Approved by ' + esc(m.approved_by) + '.' : 'Not yet approved.') + '</p>' : '<p class="small">No brief yet. Tarikh sends only the facts read from the papers (and the masked client account) to the model.</p>') +
        '<div class="acts" style="margin-top:16px"><button class="btn red" id="mkbrief">' + (br ? 'Draft again' : 'Draft the brief') + '</button>' + (br && !m.approved_by ? '<button class="btn" id="okbrief">Approve as ' + esc(LIVE ? ME.name : D.CHAMBERS.advocate) + '</button>' : '') + '</div></div></section>';
      doc.getElementById('mkbrief').addEventListener('click', function (e) { if (!LIVE) { toast('Drafting needs the Tarikh server and Azure.'); return; } e.target.innerHTML = '<span class="spin"></span> Drafting'; api('matters/' + m.id + '/brief', { json: {} }).then(function () { return api('desk/' + m.id); }).then(function (v) { D.MATTERS[D.MATTERS.findIndex(function (x) { return x.id === v.id; })] = v; renderMatter(v); }).catch(function (e2) { e.target.textContent = 'Draft the brief'; fail(e2); }); });
      var ok = doc.getElementById('okbrief'); if (ok) ok.addEventListener('click', function () { save(api('matters/' + m.id + '/approve', { json: { actor: ME.name } }).then(function () { return api('desk/' + m.id); }), 'Brief approved.'); });
    } else if (mTab === 'ask') {
      P.innerHTML = '<section class="panel"><div class="panel-h"><h2>Ask the file</h2><span>Foundry Agent Service · two read-only tools · this matter only</span></div><div class="panel-b"><div class="chat" id="chat"><div class="bubble a">Ask about this matter: its dates, its papers, what is missing.</div></div><form id="askf" class="acts" style="margin-top:14px"><label class="sr" for="aq">Question</label><input class="inp" id="aq" placeholder="When does the complaint window close?" style="flex:1"><button class="btn red" type="submit">Ask</button></form></div></section>';
      doc.getElementById('askf').addEventListener('submit', function (e) {
        e.preventDefault(); var q = doc.getElementById('aq').value.trim(); if (!q) return; var chat = doc.getElementById('chat');
        chat.insertAdjacentHTML('beforeend', '<div class="bubble q">' + esc(q) + '</div><div class="bubble a" id="pending"><span class="spin"></span></div>'); doc.getElementById('aq').value = '';
        if (!LIVE) { doc.getElementById('pending').outerHTML = '<div class="bubble a">The assistant needs the Tarikh server and Azure.</div>'; return; }
        api('matters/' + m.id + '/ask', { json: { question: q } }).then(function (a) { doc.getElementById('pending').outerHTML = '<div class="bubble a">' + esc(a.text) + (a.tool_calls && a.tool_calls.length ? '<span class="s" style="display:block;font-family:var(--mono);font-size:11px;color:var(--g600);margin-top:6px">' + a.tool_calls.map(function (t) { return esc(t.name); }).join(', ') + '</span>' : '') + '</div>'; }).catch(function (e2) { doc.getElementById('pending').outerHTML = '<div class="bubble a">' + esc(e2.message) + '</div>'; });
      });
    } else if (mTab === 'settle') {
      var st = m.settlement;
      P.innerHTML = '<div class="grid-2"><section class="panel"><div class="panel-h"><h2>Compounding cost</h2><span>2025 Supreme Court stages</span></div><div class="panel-b" data-settle-box></div></section><section class="panel"><div class="panel-h"><h2>Settlement</h2></div><div class="panel-b">' +
        (st ? '<p class="h-s">' + inr(st.total) + ' in ' + plural(st.parts, 'instalment', 'instalments') + '</p><div class="bars" style="margin-top:14px"><i style="width:' + (st.paid / st.parts * 100) + '%;background:var(--green)"></i></div><p class="small" style="margin-top:8px">' + st.paid + ' of ' + st.parts + ' paid · ' + inr(Math.round(st.total * st.paid / st.parts)) + ' received</p>' : '<p class="small">No settlement on record.</p>') +
        '<form id="sf" class="stack" style="gap:12px;margin-top:18px"><div class="grid-2" style="grid-template-columns:1fr 1fr 1fr"><div class="field"><label for="s-t">Total (₹)</label><input class="inp" id="s-t" inputmode="numeric" value="' + (st ? st.total : (m.amount || '')) + '"></div><div class="field"><label for="s-p">Instalments</label><input class="inp" id="s-p" type="number" min="1" value="' + (st ? st.parts : 1) + '"></div><div class="field"><label for="s-d">Paid so far</label><input class="inp" id="s-d" type="number" min="0" value="' + (st ? st.paid : 0) + '"></div></div><div class="acts"><button class="btn solid" type="submit">' + (st ? 'Update settlement' : 'Record settlement') + '</button></div></form></div></section></div>';
      var sb = P.querySelector('[data-settle-box]');
      sb.innerHTML = '<div class="calc" data-settle style="grid-template-columns:minmax(0,1fr)"><div class="field"><label for="st-amt">Cheque amount (₹)</label><input class="inp" id="st-amt" name="amount" inputmode="numeric" value="' + (m.amount || 0) + '"></div><fieldset class="seg" style="border:0;margin:0;padding:0"><legend style="font-size:13px;font-weight:700;margin-bottom:8px">When the accused pays</legend>' + [['0', 'Before defence evidence', '0%'], ['5', 'After defence evidence, before judgment', '5%'], ['7.5', 'In revision or appeal', '7.5%'], ['10', 'Before the Supreme Court', '10%']].map(function (o, i) { return '<label><input type="radio" name="stage" value="' + o[0] + '"' + (i === 0 ? ' checked' : '') + '><span>' + o[1] + '</span><em>' + o[2] + '</em></label>'; }).join('') + '</fieldset><div class="out" aria-live="polite"><div class="k">Compounding cost</div><div class="v red" data-o="cost"></div><p data-o="note"></p><hr><div class="k">Total to pay</div><div class="v" data-o="total" style="font-size:36px"></div></div></div>';
      var root = sb.querySelector('[data-settle]'), amt = root.querySelector('input[name=amount]'), out = root.querySelector('.out');
      function upd() { var a = +String(amt.value).replace(/[^0-9]/g, '') || 0, r = root.querySelector('input[name=stage]:checked'), p = r ? +r.value : 0, c = Math.round(a * p / 100); out.querySelector('[data-o=cost]').textContent = inr(c); out.querySelector('[data-o=total]').textContent = inr(a + c); out.querySelector('[data-o=note]').textContent = p === 0 ? 'Paid before defence evidence: compounding with no cost.' : p + ' percent of the cheque amount, as the court directs.'; }
      amt.addEventListener('input', upd); root.querySelectorAll('input[name=stage]').forEach(function (r) { r.addEventListener('change', upd); }); upd();
      doc.getElementById('sf').addEventListener('submit', function (e) { e.preventDefault(); var body = { total: +doc.getElementById('s-t').value.replace(/[^0-9]/g, ''), parts: +doc.getElementById('s-p').value, paid: +doc.getElementById('s-d').value }; if (!LIVE) { m.settlement = body; toast('Preview only: not saved.'); renderMatter(m); return; } save(api('desk/' + m.id + '/settlement', { json: body }), 'Settlement saved.'); });
    } else {
      var log = m.log || activity(m);
      P.innerHTML = '<section class="panel"><div class="panel-h"><h2>Activity</h2><span>append-only · newest first</span></div><table class="dtable"><tbody>' + log.map(function (a) { return '<tr style="cursor:default"><td><b>' + esc(a[0]) + '</b><span class="s">' + esc(a[1]) + '</span></td><td class="r"><span class="tag">' + (a[2] ? esc(new Date(a[2]).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })) : '') + '</span></td></tr>'; }).join('') + '</tbody></table></section>';
    }
  }

  /* ---------- Diary ---------- */
  var dMonth = null;
  function diary() {
    if (!D.MATTERS.length) { C.innerHTML = '<h1>Diary</h1><div style="margin-top:24px">' + emptyDesk() + '</div>'; return; }
    if (!dMonth) dMonth = [+TODAY.slice(0, 4), +TODAY.slice(5, 7) - 1];
    var y = dMonth[0], mo = dMonth[1], ev = T.eventsFor(D.MATTERS);
    var agenda = Object.keys(ev).filter(function (d) { return E.daysBetween(TODAY, d) >= 0; }).sort().slice(0, 12);
    C.innerHTML = '<div class="mhead"><div><h1>' + T.MONTH[mo] + ' ' + y + '</h1><p class="sub">Black for hearings, red for statutory deadlines, grey when a window opens. Sundays in red.</p></div>' +
      '<div class="acts"><button class="btn sm" id="dprev" aria-label="Previous month">←</button><button class="btn sm" id="dtoday">Today</button><button class="btn sm" id="dnext" aria-label="Next month">→</button></div></div>' +
      '<div class="grid-2 wide" style="margin-top:22px"><section class="panel"><div class="panel-b">' + T.monthHTML(y, mo, ev, 'matter.html') + '</div></section>' +
      '<section class="panel"><div class="panel-h"><h2>Coming up</h2></div><div class="panel-b"><ol class="tl">' + agenda.map(function (d) { return ev[d].map(function (e) { return '<li class="' + (e.cls === 'dl' ? 'next' : '') + '"><span class="d">' + T.WD[T.dow(d)].slice(0, 3) + ' ' + dshort(d) + '</span><b><a href="matter.html#' + e.id + '" style="text-decoration:none">' + esc(e.t) + '</a></b></li>'; }).join(''); }).join('') + '</ol></div></section></div>';
    function go(k) { var d = new Date(Date.UTC(dMonth[0], dMonth[1] + k, 1)); dMonth = [d.getUTCFullYear(), d.getUTCMonth()]; diary(); }
    doc.getElementById('dprev').addEventListener('click', function () { go(-1); });
    doc.getElementById('dnext').addEventListener('click', function () { go(1); });
    doc.getElementById('dtoday').addEventListener('click', function () { dMonth = null; diary(); });
  }

  /* ---------- Portfolio (Recover) ---------- */
  var pf = { stage: 'all', adv: 'all', sel: {} };
  var SC = { notice: '#E2321B', payment: '#F08A78', file: '#B92410', cognizance: '#C77C00', summons: '#E2A73B', evidence: '#0B0B0B', arguments: '#5A5A55', settled: '#17804A', decided: '#C2C2BD' };
  function asRow(m) {
    var adj = (m.hearings || []).filter(function (h) { return /Adjourned|Not served/.test(h[2]); }).length;
    var city = m.city || (m.court || '').split(',').pop().trim();
    var rec = m.settlement ? Math.round(m.settlement.total * m.settlement.paid / m.settlement.parts) : 0;
    return { id: m.id, ref: refOf(m), accused: m.accused, city: city, amount: m.amount || 0, stage: m.stage, cheque: m.cheque, presented: m.presented, memo: m.memo, sent: m.sent, delivered: m.delivered, filed: m.filed, adjournments: adj, advocate: m.advocate, next: m.next ? m.next[0] : null, recovered: rec };
  }
  function portfolio() {
    if (!D.MATTERS.length) { C.innerHTML = '<h1>Portfolio</h1><div style="margin-top:24px"><div class="empty"><p class="kicker">No matters yet</p><h2 class="h-m">Import a return file.</h2><p class="small" style="max-width:560px">One row per bounced cheque: drawer, amount and the dates you have. Tarikh opens a matter for each row and counts its deadlines.</p><div class="acts"><button class="btn red" id="imp">Import a return file</button><button class="btn" id="load-samples">Load sample matters</button></div></div></div>' + importDialog(); wireImport(); return; }
    var P = D.MATTERS.map(asRow), total = 0, rec = 0, filed = P.filter(function (r) { return r.filed; }), adjs = 0;
    P.forEach(function (r) { total += r.amount; rec += r.recovered; }); filed.forEach(function (r) { adjs += r.adjournments; });
    if (!filed.length) filed = [{ adjournments: 0 }];
    var openW = P.filter(function (r) { return r.stage === 'file'; }).length, un = P.filter(function (r) { return !r.advocate; }).length;
    var counts = {}; D.STAGES.forEach(function (s) { counts[s.k] = 0; }); P.forEach(function (r) { counts[r.stage]++; });
    var age = [['Under 6 months', 0, 182], ['6 to 12 months', 183, 365], ['1 to 2 years', 366, 730], ['Over 2 years', 731, 1e6]].map(function (b) { return [b[0], filed.filter(function (r) { if (!r.filed) return false; var a = E.daysBetween(r.filed, TODAY); return a >= b[1] && a <= b[2]; }).length]; });
    var rows = P.filter(function (r) { return (pf.stage === 'all' || r.stage === pf.stage) && (pf.adv === 'all' || (pf.adv === 'none' ? !r.advocate : r.advocate === pf.adv)); });
    var nsel = Object.keys(pf.sel).filter(function (k) { return pf.sel[k]; }).length;
    function rowStatus(r) {
      if (r.stage === 'notice' || r.stage === 'payment' || r.stage === 'file') return T.statusOf({ cheque: r.cheque, presented: r.presented, memo: r.memo, sent: r.sent, delivered: r.delivered, stage: r.stage });
      if (r.stage === 'settled') return { cls: 'ok', text: 'Settled' };
      if (r.stage === 'decided') return { cls: 'gone', text: 'Decided' };
      return { cls: '', text: T.STAGE_LABEL[r.stage] };
    }
    C.innerHTML = '<div class="mhead"><div><p class="tiny" style="font-family:var(--mono)">TARIKH RECOVER</p><h1 style="margin-top:8px">' + esc(D.CHAMBERS.name) + '</h1><p class="sub">' + plural(P.length, 'matter', 'matters') + ' across ' + plural(new Set(P.map(function (r) { return r.city; }).filter(Boolean)).size, 'city', 'cities') + '.</p></div><div class="acts"><button class="btn sm" id="imp">Import a return file</button><button class="btn sm solid" id="exp">Copy summary</button></div></div>' +
      '<div class="kpis six" style="margin-top:24px">' +
      [['Matters', P.length, ''], ['At stake', D.lakh(total), ''], ['Recovered', D.lakh(rec), ''], ['Windows open', openW, 'hot'], ['Adjournments per filed case', (adjs / filed.length).toFixed(1), ''], ['Unassigned', un, '']].map(function (k) { return '<div class="kpi ' + k[2] + '"><div class="k">' + k[0] + '</div><div class="v" style="font-size:26px">' + k[1] + '</div></div>'; }).join('') + '</div>' +
      '<div class="grid-2" style="margin-top:16px"><section class="panel"><div class="panel-h"><h2>By stage</h2><span>share of matters</span></div><div class="panel-b"><div class="bars" role="img" aria-label="' + D.STAGES.map(function (s) { return s.label + ' ' + counts[s.k]; }).join(', ') + '">' + D.STAGES.map(function (s) { return '<i style="width:' + (counts[s.k] / P.length * 100) + '%;background:' + SC[s.k] + '" title="' + s.label + ': ' + counts[s.k] + '"></i>'; }).join('') + '</div><div class="legend2">' + D.STAGES.map(function (s) { return '<span><i style="background:' + SC[s.k] + '"></i>' + s.label + ' ' + counts[s.k] + '</span>'; }).join('') + '</div></div></section>' +
      '<section class="panel"><div class="panel-h"><h2>Age of filed cases</h2><span>since filing</span></div><div class="panel-b stack" style="gap:10px">' + age.map(function (a) { return '<div style="display:grid;grid-template-columns:120px 1fr 28px;gap:10px;align-items:center;font-size:13px"><span>' + a[0] + '</span><div class="bars" style="height:10px"><i style="width:' + (a[1] / filed.length * 100) + '%;background:' + (a[0] === 'Over 2 years' ? 'var(--red)' : 'var(--bk)') + '"></i></div><b style="text-align:right">' + a[1] + '</b></div>'; }).join('') + '</div></section></div>' +
      '<div class="filters" style="margin:22px 0 14px"><label class="small" for="fs">Stage</label><select class="sel sm" id="fs"><option value="all">All stages</option>' + D.STAGES.map(function (s) { return '<option value="' + s.k + '"' + (pf.stage === s.k ? ' selected' : '') + '>' + s.label + ' (' + counts[s.k] + ')</option>'; }).join('') + '</select>' +
      '<label class="small" for="fa">Advocate</label><select class="sel sm" id="fa"><option value="all">Everyone</option><option value="none"' + (pf.adv === 'none' ? ' selected' : '') + '>Unassigned</option>' + D.PANEL.map(function (a) { return '<option' + (pf.adv === a ? ' selected' : '') + '>' + a + '</option>'; }).join('') + '</select><span class="small">' + rows.length + ' shown</span></div>' +
      '<section class="panel scroll"><div class="bulk"' + (nsel ? '' : ' hidden') + '><b>' + nsel + ' selected</b><label class="sr" for="ba">Assign to</label><select class="sel sm" id="ba">' + D.PANEL.map(function (a) { return '<option>' + a + '</option>'; }).join('') + '</select><button class="btn sm red" id="bgo">Assign</button><button class="btn sm" id="bclr" style="color:#fff">Clear</button></div>' +
      '<table class="dtable"><thead><tr><th scope="col"><input type="checkbox" id="sall" aria-label="Select all shown"' + (rows.length && rows.every(function (r) { return pf.sel[r.id]; }) ? ' checked' : '') + '></th><th scope="col">Borrower</th><th scope="col" class="hide-sm">Court</th><th scope="col" class="r">Amount</th><th scope="col">Stage</th><th scope="col" class="hide-sm">Next</th><th scope="col" class="hide-sm">Advocate</th></tr></thead><tbody>' +
      rows.map(function (r) { var s = rowStatus(r); return '<tr data-id="' + r.id + '"><td><input type="checkbox" aria-label="Select ' + esc(r.accused) + '"' + (pf.sel[r.id] ? ' checked' : '') + '></td><td><b>' + esc(r.accused) + '</b><span class="s">' + esc(r.ref || r.id) + (r.filed ? ' · filed ' + dshort(r.filed) + ' ' + r.filed.slice(0, 4) + ' · ' + plural(r.adjournments, 'adjournment', 'adjournments') : '') + '</span></td><td class="hide-sm">' + r.city + '</td><td class="r">' + inr(r.amount) + '</td><td>' + T.chip(s) + '</td><td class="hide-sm">' + (r.next ? dshort(r.next) : '<span class="s">–</span>') + '</td><td class="hide-sm">' + (r.advocate ? esc(r.advocate) : '<span class="chip warn plain">Unassigned</span>') + '</td></tr>'; }).join('') + '</tbody></table></section>' +
      '<p class="tiny" style="margin-top:12px">Click a row to select it. Selected matters can be allocated to a panel advocate.</p>' +
      importDialog();
    doc.getElementById('fs').addEventListener('change', function (e) { pf.stage = e.target.value; portfolio(); });
    doc.getElementById('fa').addEventListener('change', function (e) { pf.adv = e.target.value; portfolio(); });
    C.querySelectorAll('tbody tr[data-id]').forEach(function (tr) { tr.addEventListener('click', function (e) { var id = tr.getAttribute('data-id'); if (e.target.closest('a')) return; if (e.target.type !== 'checkbox') { var cb = tr.querySelector('input'); cb.checked = !cb.checked; } pf.sel[id] = tr.querySelector('input').checked; portfolio(); }); });
    doc.getElementById('sall').addEventListener('change', function (e) { rows.forEach(function (r) { pf.sel[r.id] = e.target.checked; }); portfolio(); });
    var bgo = doc.getElementById('bgo');
    if (bgo) { bgo.addEventListener('click', function () { var a = doc.getElementById('ba').value, ids = Object.keys(pf.sel).filter(function (k) { return pf.sel[k]; });
      if (!LIVE) { D.MATTERS.forEach(function (m) { if (pf.sel[m.id]) m.advocate = a; }); pf.sel = {}; portfolio(); toast('Preview only: not saved.'); return; }
      api('desk/assign', { json: { ids: ids, advocate: a } }).then(function () { pf.sel = {}; toast(plural(ids.length, 'matter', 'matters') + ' allocated to ' + a + '.'); reload(); }).catch(fail); });
      doc.getElementById('bclr').addEventListener('click', function () { pf.sel = {}; portfolio(); }); }
    wireImport();
    doc.getElementById('exp').addEventListener('click', function () {
      var txt = 'Portfolio, ' + dlong(TODAY) + '\n' + D.STAGES.map(function (s) { return s.label + ': ' + counts[s.k]; }).join('\n') + '\nAt stake: ' + inr(total) + '\nRecovered: ' + inr(rec);
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(function () { toast('Summary copied.'); }, function () { toast('Copying is blocked here.'); }); else toast('Copying is blocked here.');
    });
  }

  function importDialog() {
    return '<dialog class="modal" id="impd" aria-labelledby="impt"><div class="panel-h"><h2 id="impt">Import a return file</h2><button class="btn sm" id="impx" type="button">Close</button></div><div class="panel-b stack">' +
      '<p class="small">A CSV with a header row. Required: <code>drawer</code>. Optional: <code>reference, city, amount, cheque_number, cheque_date, presented_on, memo_received_on, notice_sent_on, notice_delivered_on</code>. Dates as YYYY-MM-DD. A row with a bad date is skipped and reported, never repaired.</p>' +
      '<div class="field"><label for="impf">CSV file</label><input type="file" id="impf" accept=".csv,text/csv"></div><div class="field"><label for="impt2">Or paste the rows</label><textarea class="inp" id="impt2" placeholder="drawer,amount,cheque_date&#10;Ahuja Tyres,145000,2026-11-01"></textarea></div>' +
      '<p class="err" id="impe" role="alert" style="color:var(--red);font-size:13px;font-weight:650"></p><div class="acts"><button class="btn red" id="impgo" type="button">Import</button><button class="btn" id="impsample" type="button">Import the sample return file (24 rows)</button></div></div></dialog>';
  }
  function wireImport() {
    if (!doc.getElementById('impd')) C.insertAdjacentHTML('beforeend', importDialog());
    var dlg = doc.getElementById('impd'), open = doc.getElementById('imp');
    if (open) open.addEventListener('click', function () { dlg.showModal(); });
    doc.getElementById('impx').addEventListener('click', function () { dlg.close(); });
    function done(r) { dlg.close(); toast(plural(r.created, 'matter', 'matters') + ' opened' + (r.problems.length ? '; ' + plural(r.problems.length, 'row', 'rows') + ' skipped' : '') + '.'); if (r.problems.length) setTimeout(function () { alertRows(r.problems); }, 300); reload(); }
    function alertRows(p) { C.insertAdjacentHTML('afterbegin', '<div class="notice" style="margin-bottom:16px"><b>Skipped rows</b><span>' + p.map(esc).join(' ') + '</span></div>'); }
    doc.getElementById('impgo').addEventListener('click', function () {
      if (!LIVE) { doc.getElementById('impe').textContent = 'Importing needs the Tarikh server.'; return; }
      var f = doc.getElementById('impf').files[0], t = doc.getElementById('impt2').value;
      var go = function (csv) { if (!csv.trim()) { doc.getElementById('impe').textContent = 'Choose a file or paste rows first.'; return; } api('desk/import', { json: { csv: csv } }).then(done).catch(function (e) { doc.getElementById('impe').textContent = e.message; }); };
      if (f) { var rd = new FileReader(); rd.onload = function () { go(String(rd.result)); }; rd.readAsText(f); } else go(t);
    });
    doc.getElementById('impsample').addEventListener('click', function () { if (!LIVE) { doc.getElementById('impe').textContent = 'Importing needs the Tarikh server.'; return; } api('desk/import', { json: { sample: true } }).then(done).catch(fail); });
  }

  /* ---------- Drafts ---------- */
  var dSel = 'notice';
  function fx(v, kind) { return v ? '<span class="fx' + (kind ? ' ' + kind : '') + '">' + esc(v) + '</span>' : '<span class="fx entry">[to be entered]</span>'; }
  var DOCS = [
    ['notice', 'Demand notice', 'Section 138(b)'], ['complaint', 'Complaint synopsis', 'After the index'], ['contacts', 'Affidavit of contact details', 'At filing, 2025 directions'],
    ['s143a', 'Interim compensation', 'Section 143A'], ['s145', 'Evidence affidavit', 'Section 145'], ['s147', 'Joint application to compound', 'Section 147'], ['delay', 'Condonation of delay', 'Proviso to Section 142(1)(b)']
  ];
  function draftBody(k, m) {
    var w = T.windowsOf(m), A = fx(inr(m.amount)), adv = D.CHAMBERS.advocate;
    var head = { notice: ['Legal notice', 'Under Section 138 of the Negotiable Instruments Act, 1881'], complaint: ['Synopsis', 'Complaint under Section 138 read with Section 142, Negotiable Instruments Act, 1881'], contacts: ['Affidavit', 'Contact details of the accused, filed with the complaint'], s143a: ['Application under Section 143A', 'Negotiable Instruments Act, 1881, for interim compensation'], s145: ['Affidavit of evidence', 'Under Section 145, Negotiable Instruments Act, 1881'], s147: ['Joint application', 'For compounding under Section 147, Negotiable Instruments Act, 1881'], delay: ['Application for condonation of delay', 'Proviso to Section 142(1)(b), Negotiable Instruments Act, 1881'] }[k];
    var court = '<p class="sub">In the court of the ' + esc(m.court) + (m.caseNo ? ' · ' + esc(m.caseNo) : '') + '</p><p class="sub">' + esc(m.complainant) + ' v. ' + esc(m.accused) + '</p>';
    var b = '<h4>' + head[0] + '</h4><p class="sub">' + head[1] + '</p>' + (k === 'notice' ? '' : court);
    if (k === 'notice') b += '<p>To,<br>' + fx(m.accused) + '</p><p>Under instructions from my client ' + fx(m.complainant) + ', I give you notice as follows:</p><ol><li>You drew cheque number ' + fx(m.chequeNo) + ' dated ' + fx(dot(m.cheque)) + ' for ' + A + ' on ' + fx(m.bank) + ' in favour of my client, towards a debt or liability owed to my client.</li><li>My client presented the cheque on ' + fx(dot(m.presented)) + '. It was returned unpaid on ' + fx(dot(m.returned)) + ' with the reason “' + fx(m.reason) + '”. The return memo reached my client on ' + fx(dot(m.memo), 'entry') + '.</li><li>I call upon you to pay ' + A + ' to my client within fifteen days of receiving this notice. If you do not, my client will file a complaint under Section 138 read with Section 142 of the Act.</li></ol><p class="sig">' + esc(adv) + '<br>Advocate for the complainant</p>';
    else if (k === 'complaint') b += '<table class="syn"><tbody><tr><td>Complainant</td><td>' + fx(m.complainant) + '</td></tr><tr><td>Accused</td><td>' + fx(m.accused) + '</td></tr><tr><td>Cheque number, date, amount</td><td>' + fx(m.chequeNo) + ', ' + fx(dot(m.cheque)) + ', ' + A + '</td></tr><tr><td>Drawn on</td><td>' + fx(m.bank) + '</td></tr><tr><td>Presented, returned, reason</td><td>' + fx(dot(m.presented)) + ', ' + fx(dot(m.returned)) + ', ' + fx(m.reason) + '</td></tr><tr><td>Return memo received</td><td>' + fx(dot(m.memo), 'entry') + '</td></tr><tr><td>Notice sent and served</td><td>' + fx(dot(m.sent)) + ', ' + fx(dot(m.delivered), 'entry') + '</td></tr><tr><td>Fifteen days to pay ended</td><td>' + fx(dot(w.payment.closes), 'calc') + '</td></tr><tr><td>Cause of action</td><td>' + fx(dot(w.complaint.opens), 'calc') + '</td></tr><tr><td>Last day to file</td><td>' + fx(dot(w.complaint.closes), 'calc') + '</td></tr><tr><td>Accused’s email and mobile</td><td>' + fx(m.email, 'entry') + ', ' + fx(m.phone, 'entry') + '</td></tr></tbody></table><p class="tiny">Check the field order against the format the Supreme Court prescribed in Sanjabij Tari (2025).</p>';
    else if (k === 'contacts') b += '<p>I, the authorised representative of ' + fx(m.complainant) + ', state on oath:</p><ol><li>The email address of the accused known to the complainant is ' + fx(m.email, 'entry') + '.</li><li>The mobile number of the accused, also used for messaging, is ' + fx(m.phone, 'entry') + '.</li><li>These details are true to my knowledge. I will inform the court promptly of any change that comes to my notice.</li></ol><p class="sig">Deponent</p>';
    else if (k === 's143a') b += '<ol><li>The complainant has filed this complaint over cheque number ' + fx(m.chequeNo) + ' for ' + A + '.</li><li>Section 143A allows the court to direct the accused to pay interim compensation of up to twenty percent of the cheque amount.</li><li>The complainant prays that the accused be directed to pay interim compensation of ' + fx(inr(Math.round(m.amount * 0.2)), 'calc') + ', being twenty percent of the cheque amount, within sixty days.</li></ol><p class="sig">' + esc(adv) + '<br>Advocate for the complainant</p>';
    else if (k === 's145') b += '<p>I, the authorised representative of ' + fx(m.complainant) + ', state on oath:</p><ol><li>The accused issued cheque number ' + fx(m.chequeNo) + ' dated ' + fx(dot(m.cheque)) + ' for ' + A + ' towards a debt owed to the complainant.</li><li>The cheque was returned unpaid on ' + fx(dot(m.returned)) + ' with the reason “' + fx(m.reason) + '”.</li><li>The demand notice dated ' + fx(dot(m.sent)) + ' was served on ' + fx(dot(m.delivered), 'entry') + '. The accused did not pay within fifteen days.</li><li>The cheque, return memo, notice and postal proof are exhibited with this affidavit.</li></ol><p class="sig">Deponent</p>';
    else if (k === 's147') b += '<ol><li>The parties have settled the matter for ' + fx(inr(m.settlement ? m.settlement.total : m.amount)) + (m.settlement ? ', payable in ' + fx(String(m.settlement.parts), 'calc') + ' instalments' : '') + '.</li><li>The offence is compoundable under Section 147 of the Act.</li><li>The parties pray that the offence be compounded and the accused acquitted, on such costs as the court directs under the 2025 guidelines.</li></ol><p class="sig">Complainant · Accused</p>';
    else b += '<ol><li>The complaint window ran from ' + fx(dot(w.complaint.opens), 'calc') + ' to ' + fx(dot(w.complaint.closes), 'calc') + '.</li><li>The complaint is filed ' + fx(w.complaint.status === 'expired' ? plural(E.daysBetween(w.complaint.closes, TODAY), 'day', 'days') + ' late' : 'within time', 'calc') + '.</li><li>The delay occurred because ' + fx(null) + '.</li><li>The complainant prays that the delay be condoned for sufficient cause.</li></ol><p class="sig">' + esc(adv) + '<br>Advocate for the complainant</p>';
    return b;
  }
  function drafts() {
    if (!D.MATTERS.length) { C.innerHTML = '<h1>Drafts</h1><div style="margin-top:24px">' + emptyDesk() + '</div>'; return; }
    var id = (location.hash || '').slice(1), m = D.find(id) || D.MATTERS[0];
    C.innerHTML = '<div class="mhead"><div><h1>Drafts</h1><p class="sub">Built only from facts with a source. Nothing leaves draft until an advocate approves it.</p></div><div class="field"><label for="dm">Matter</label><select class="sel sm" id="dm">' + D.MATTERS.map(function (x) { return '<option value="' + x.id + '"' + (x.id === m.id ? ' selected' : '') + '>' + esc(x.accused) + ' · ' + esc(refOf(x)) + '</option>'; }).join('') + '</select></div></div>' +
      '<div class="doc-wrap" style="margin-top:22px"><nav class="panel doclist" style="padding:8px" aria-label="Documents">' + DOCS.map(function (d) { return '<button type="button" data-d="' + d[0] + '" aria-pressed="' + (dSel === d[0]) + '">' + d[1] + '<span>' + d[2] + '</span></button>'; }).join('') + '</nav>' +
      '<div class="stack"><div class="doc" id="docbody">' + draftBody(dSel, m) + '</div><div class="legend"><span><span class="fx">red</span> read from a paper</span><span><span class="fx entry">amber</span> entered, or still to enter</span><span><span class="fx calc">grey</span> counted by rule</span></div>' +
      '<section class="panel"><div class="panel-b"><form id="apf" class="stack" style="gap:12px" novalidate><div class="field"><label for="apn">Advocate’s name</label><input class="inp" id="apn" autocomplete="off" placeholder="' + D.CHAMBERS.advocate + '"></div><label style="display:flex;gap:10px;align-items:flex-start;font-size:14px"><input type="checkbox" id="apc" style="width:18px;height:18px;accent-color:var(--red);margin-top:2px">I have checked every marked fact against its source.</label><p class="err" id="ape" role="alert" style="color:var(--red);font-weight:650;font-size:13px"></p><div class="acts"><button class="btn red" type="submit">Approve draft</button><button class="btn" type="button" id="cpy">Copy text</button></div></form></div></section></div></div>';
    doc.getElementById('dm').addEventListener('change', function (e) { history.replaceState(null, '', '#' + e.target.value); drafts(); });
    C.querySelectorAll('.doclist button').forEach(function (b) { b.addEventListener('click', function () { dSel = b.getAttribute('data-d'); drafts(); }); });
    doc.getElementById('apf').addEventListener('submit', function (e) {
      e.preventDefault(); var n = doc.getElementById('apn').value.trim(), c = doc.getElementById('apc').checked, er = doc.getElementById('ape');
      if (!n) { er.textContent = 'Type your name to approve.'; doc.getElementById('apn').focus(); return; }
      if (!c) { er.textContent = 'Tick the box to confirm you checked each fact.'; doc.getElementById('apc').focus(); return; }
      if (doc.querySelector('#docbody .fx.entry') && /\[to be entered\]/.test(doc.getElementById('docbody').textContent)) { er.textContent = 'Some facts are still to be entered. Fill them in before approving.'; return; }
      er.textContent = ''; var t = DOCS.filter(function (d) { return d[0] === dSel; })[0][1];
      if (LIVE) { api('desk/' + m.id + '/drafts/approve', { json: { title: t, actor: n } }).then(function (v) { D.MATTERS[D.MATTERS.findIndex(function (x) { return x.id === v.id; })] = v; setCounts(); toast('Approved by ' + n + ' and recorded in the activity log. Nothing is filed or sent.'); }).catch(fail); return; }
      var found = (m.drafts = m.drafts || []).filter(function (d) { return d.t.indexOf(t.split(' ')[0]) === 0; })[0];
      if (found) found.s = 'Approved'; else m.drafts.push({ t: t, s: 'Approved' });
      setCounts(); toast('Preview only: approval not saved.');
    });
    doc.getElementById('cpy').addEventListener('click', function () {
      var txt = doc.getElementById('docbody').innerText;
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(function () { toast('Draft text copied.'); }, function () { toast('Copying is blocked here. Select the text instead.'); });
      else toast('Copying is blocked here. Select the text instead.');
    });
  }

  /* ---------- Router ---------- */
  function render() { ({ today: today, matters: matters, matter: matter, diary: diary, portfolio: portfolio, drafts: drafts })[page](); }
  C.addEventListener('click', function (e) { var tr = e.target.closest('tr[data-href]'); if (tr && !e.target.closest('a,button,input')) location.href = tr.getAttribute('data-href'); });
  window.addEventListener('hashchange', function () { if (page === 'matter' || page === 'drafts') { mTab = 'clocks'; render(); window.scrollTo(0, 0); } });
  if (page === 'matter') { try { var qs = new URLSearchParams(location.search).get('tab'); if (qs) mTab = qs; } catch (e) {} }
  boot();
})();
