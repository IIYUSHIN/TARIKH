/* Tarikh demo desk. Renders every app screen from TarikhData; statuses come from TarikhEngine.
   Nothing is saved: changes live in memory until the page is closed. */
(function () {
  'use strict';
  var E = window.TarikhEngine, D = window.TarikhData, T = window.Tarikh, doc = document;
  var app = doc.getElementById('app'); if (!app) return;
  var page = app.getAttribute('data-page'), C = doc.getElementById('content');
  var esc = T.esc, plural = T.plural, dshort = T.dshort, dlong = T.dlong, inr = D.inr, TODAY = D.TODAY;
  function dot(iso) { return iso ? iso.slice(8) + '.' + iso.slice(5, 7) + '.' + iso.slice(0, 4) : ''; }
  function within(iso, a, b) { var k = E.daysBetween(TODAY, iso); return k >= a && k <= b; }
  function toast(msg) { var t = doc.createElement('div'); t.className = 'toast'; t.setAttribute('role', 'status'); t.textContent = msg; doc.body.appendChild(t); setTimeout(function () { t.remove(); }, 2600); }
  function matterLink(m) { return 'matter.html#' + m.id; }
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
  setCounts();
  var pal = doc.getElementById('palette'), pq = doc.getElementById('palette-q'), pl = doc.getElementById('palette-list'), psel = 0;
  var PAGES = [['Today', 'index.html'], ['Matters', 'matters.html'], ['Diary', 'diary.html'], ['Drafts', 'drafts.html'], ['Portfolio (Recover)', 'portfolio.html'], ['Check a cheque', '../check.html'], ['Rule register', '../law.html']];
  function palRender() {
    var q = pq.value.trim().toLowerCase(), h = '', items = [];
    var ms = D.MATTERS.filter(function (m) { return !q || (m.id + ' ' + m.accused + ' ' + m.complainant + ' ' + (m.caseNo || '') + ' ' + m.court).toLowerCase().indexOf(q) >= 0; }).slice(0, 7);
    var ps = PAGES.filter(function (p) { return !q || p[0].toLowerCase().indexOf(q) >= 0; });
    if (ms.length) { h += '<li class="ph">Matters</li>'; ms.forEach(function (m) { items.push(matterLink(m)); h += '<li><a role="option" href="' + matterLink(m) + '"><b>' + esc(m.accused) + '</b><span>' + m.id + ' · ' + esc(T.statusOf(m).text) + '</span></a></li>'; }); }
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

  /* ---------- Today ---------- */
  function today() {
    var r = ranked(), pre = r.filter(function (x) { return !x.m.filed && x.m.stage !== 'settled' && x.s.cls !== 'gone'; });
    var hear = D.MATTERS.filter(function (m) { return m.next && within(m.next[0], 0, 21); }).sort(function (a, b) { return a.next[0] < b.next[0] ? -1 : 1; });
    var waits = draftsWaiting(), missing = D.MATTERS.filter(function (m) { return !m.memo || (m.sent && !m.delivered); });
    var gone = r.filter(function (x) { return !x.m.filed && x.s.cls === 'gone'; });
    var hot = pre.filter(function (x) { return x.s.cls === 'hot'; });
    C.innerHTML =
      '<div class="mhead"><div><h1>Good morning. ' + (hot.length ? plural(hot.length, 'deadline needs', 'deadlines need') + ' you this week.' : 'Nothing is closing this week.') + '</h1><p class="sub">' + T.WD[T.dow(TODAY)] + ', ' + dlong(TODAY) + ' · ' + esc(D.CHAMBERS.name) + '</p></div>' +
      '<div style="--lw:118px">' + T.leafHTML(TODAY, 'Today', '') + '</div></div>' +
      '<div class="kpis" style="margin-top:20px">' +
      '<a class="kpi hot" href="matters.html"><div class="k">Closing in 7 days</div><div class="v">' + hot.length + '</div><div class="s">complaint or notice deadlines</div></a>' +
      '<a class="kpi" href="diary.html"><div class="k">Hearings, next 7 days</div><div class="v">' + hear.filter(function (m) { return within(m.next[0], 0, 7); }).length + '</div><div class="s">across ' + plural(new Set(hear.map(function (m) { return m.court; })).size, 'court', 'courts') + '</div></a>' +
      '<a class="kpi" href="drafts.html"><div class="k">Drafts to approve</div><div class="v">' + waits.length + '</div><div class="s">only an advocate can approve</div></a>' +
      '<a class="kpi" href="#missing"><div class="k">Dates to enter</div><div class="v">' + missing.length + '</div><div class="s">on no paper, so asked</div></a></div>' +
      '<div class="grid-2" style="margin-top:16px"><div class="stack">' +
      '<section class="panel"><div class="panel-h"><h2>Deadlines, most urgent first</h2><span>counted by rule</span></div>' +
      '<table class="dtable"><tbody>' + pre.map(function (x) { return '<tr data-href="' + matterLink(x.m) + '"><td><b>' + esc(x.m.accused) + '</b><span class="s">' + x.m.id + ' · ' + esc(x.m.complainant) + '</span></td><td class="hide-sm">' + (x.s.key ? '<b>' + dshort(x.s.key) + '</b><span class="s">' + esc(x.s.keyLabel) + '</span>' : '<span class="s">' + esc(x.s.keyLabel) + '</span>') + '</td><td class="r">' + T.chip(x.s) + '</td></tr>'; }).join('') + '</tbody></table></section>' +
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
    C.innerHTML = '<h1>Matters</h1><p class="sub">Ordered by what runs out first. Click a matter to open it.</p>' +
      '<div class="filters" style="margin:22px 0 14px">' + names.map(function (n) { return '<button class="fbtn" data-f="' + n[0] + '" aria-pressed="' + (mFilter === n[0]) + '">' + n[1] + '<em>' + D.MATTERS.filter(groups[n[0]]).length + '</em></button>'; }).join('') +
      '<span style="flex:1"></span><label class="sr" for="mq">Filter matters</label><input class="inp sm" id="mq" placeholder="Filter by party or court" value="' + esc(mQuery) + '"></div>' +
      '<section class="panel"><table class="dtable"><thead><tr><th scope="col">Matter</th><th scope="col" class="hide-sm">Court</th><th scope="col" class="r hide-sm">Amount</th><th scope="col" class="hide-sm">Key date</th><th scope="col" class="r">Status</th></tr></thead><tbody>' +
      (rows.length ? rows.map(function (x) { var m = x.m; return '<tr data-href="' + matterLink(m) + '"><td><b>' + esc(m.accused) + '</b><span class="s">' + m.id + ' · ' + esc(m.complainant) + (m.caseNo ? ' · ' + m.caseNo : '') + '</span></td><td class="hide-sm">' + esc(m.court.replace('Judicial Magistrate First Class, ', 'JMIC, ')) + '</td><td class="r hide-sm">' + inr(m.amount) + '</td><td class="hide-sm">' + (x.s.key ? '<b>' + dshort(x.s.key) + '</b><span class="s">' + esc(x.s.keyLabel) + '</span>' : '<span class="s">' + esc(x.s.keyLabel) + '</span>') + '</td><td class="r">' + T.chip(x.s) + '</td></tr>'; }).join('') : '<tr><td colspan="5"><p class="small">No matters match. Clear the filter to see all ' + D.MATTERS.length + '.</p></td></tr>') +
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
    var id = (location.hash || '#KF-1042').slice(1), m = D.find(id) || D.MATTERS[0], s = T.statusOf(m), w = s.windows;
    doc.title = m.accused + ' · Demo · Tarikh';
    var leafDate = m.next ? m.next[0] : s.key, leafLabel = m.next ? 'Next hearing' : s.keyLabel;
    var tabs = [['clocks', 'Clocks'], ['facts', 'Facts and papers'], ['hearings', 'Hearings'], ['drafts', 'Drafts'], ['settle', 'Settlement'], ['activity', 'Activity']];
    C.innerHTML = '<div class="mhead"><div><p class="tiny" style="font-family:var(--mono)"><a href="matters.html">Matters</a> / ' + m.id + '</p><h1 style="margin-top:8px">' + esc(m.complainant) + ' <span style="color:var(--g400)">v.</span> ' + esc(m.accused) + '</h1>' +
      '<div class="meta"><span>Cheque <b>' + m.chequeNo + '</b></span><span>Amount <b>' + inr(m.amount) + '</b></span><span>' + esc(m.court) + '</span>' + (m.caseNo ? '<span>Case <b>' + m.caseNo + '</b></span>' : '') + '<span>' + T.chip(s) + '</span></div></div>' +
      (leafDate ? '<div style="--lw:150px">' + T.leafHTML(leafDate, leafLabel.length > 22 ? leafLabel.slice(0, 22) + '…' : leafLabel, '') + '</div>' : '') + '</div>' +
      '<div class="tabs" role="tablist" style="margin-top:24px">' + tabs.map(function (t) { return '<button role="tab" data-t="' + t[0] + '" aria-selected="' + (mTab === t[0]) + '">' + t[1] + '</button>'; }).join('') + '</div>' +
      '<div id="mt" style="margin-top:18px"></div>';
    C.querySelectorAll('.tabs button').forEach(function (b) { b.addEventListener('click', function () { mTab = b.getAttribute('data-t'); matter(); }); });
    var P = doc.getElementById('mt');
    if (mTab === 'clocks') {
      if (m.filed) {
        P.innerHTML = '<section class="panel"><div class="panel-b"><p class="kicker">Filed</p><p class="h-m" style="margin-top:12px">Filed on ' + dlong(m.filed) + ', inside the window.</p><p class="small" style="margin-top:8px">The complaint window ran from ' + dlong(w.complaint.opens) + ' to ' + dlong(w.complaint.closes) + '. The clocks below are the pre-filing record.</p></div></section><section class="panel" style="margin-top:16px"><div class="panel-b" id="ltbox"></div></section>';
      } else if (!m.memo || !m.sent || !m.delivered) {
        P.innerHTML = '<section class="panel"><div class="panel-h"><h2>Dates the clocks need</h2><span>none of these is printed on a paper</span></div><div class="panel-b"><form id="dates" class="stack" style="max-width:560px">' +
          [['memo', 'Return memo reached the client'], ['sent', 'Demand notice sent'], ['delivered', 'Drawer received the notice']].map(function (f) { return '<div class="field"><label for="f-' + f[0] + '">' + f[1] + '</label><input class="inp" type="date" id="f-' + f[0] + '" value="' + (m[f[0]] || '') + '"></div>'; }).join('') +
          '<div class="acts"><button class="btn solid" type="submit">Save and count</button></div></form>' +
          '<div style="margin-top:22px">' + (w.notice.closes ? '<p class="h-s">Notice must go by ' + dlong(w.notice.closes) + '.</p><p class="small">Thirty days from the day the memo reached the client.</p>' : '<p class="h-s">Enter when the memo reached the client to start the clocks.</p>') + '</div></div></section>';
        doc.getElementById('dates').addEventListener('submit', function (e) { e.preventDefault(); ['memo', 'sent', 'delivered'].forEach(function (k) { m[k] = doc.getElementById('f-' + k).value || null; }); m.missing = null; (m.log = m.log || []).unshift(['Dates entered', D.CHAMBERS.advocate]); toast('Dates saved for this session. Clocks recounted.'); setCounts(); matter(); });
        return;
      } else P.innerHTML = '<section class="panel"><div class="panel-b" id="ltbox"></div></section>';
      var box = doc.getElementById('ltbox'), lt = doc.createElement('div');
      ['cheque', 'presented', 'memo', 'sent', 'delivered'].forEach(function (k) { lt.setAttribute('data-' + k, m[k]); });
      lt.setAttribute('data-today', m.filed ? m.filed : TODAY); lt.setAttribute('data-heading', 'Move the dates'); lt.setAttribute('data-sub', 'What-if only. Nothing here changes the matter.');
      box.appendChild(lt); T.mountLongTable(lt);
    } else if (mTab === 'facts') {
      var f = [['Cheque number', m.chequeNo, 'Cheque'], ['Date on the cheque', dlong(m.cheque), 'Cheque'], ['Amount', inr(m.amount), 'Cheque'], ['Drawn on', m.bank, 'Cheque'], ['Presented', dlong(m.presented), 'Return memo'], ['Returned', dlong(m.returned), 'Return memo'], ['Reason', m.reason, 'Return memo'], ['Memo reached client', m.memo ? dlong(m.memo) : null, 'Entry'], ['Notice sent', m.sent ? dlong(m.sent) : null, 'Demand notice'], ['Notice received', m.delivered ? dlong(m.delivered) : null, 'Entry'], ['Accused email', m.email || null, 'Entry'], ['Accused mobile', m.phone || null, 'Entry']];
      P.innerHTML = '<div class="grid-2"><section class="panel"><div class="panel-h"><h2>Facts</h2><span>each with its source</span></div><div class="panel-b"><table class="fields"><tbody>' + f.map(function (r) { return '<tr><td>' + r[0] + '</td><td class="v">' + (r[1] ? esc(r[1]) : '<span class="chip warn plain">to be entered</span>') + '</td><td class="s">' + (r[2] === 'Entry' ? '<span class="chip warn plain">entry</span>' : '<span class="tag">' + r[2].toLowerCase() + '</span>') + '</td></tr>'; }).join('') + '</tbody></table></div></section>' +
        '<section class="panel"><div class="panel-h"><h2>Papers</h2><span>' + (m.papers ? '3 papers' : 'sample matter') + '</span></div><div class="panel-b stack">' + (m.papers ? '<div class="paper"><img src="../assets/img/cheque.jpg" alt="Fictional cheque 004718" loading="lazy"></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:12px"><div class="paper"><img src="../assets/img/return_memo.jpg" alt="Fictional return memo" loading="lazy"></div><div class="paper"><img src="../assets/img/demand_notice.jpg" alt="Fictional demand notice" loading="lazy"></div></div>' : '<p class="small">Papers are attached only to the Kalra Fabricators sample. In a live desk, every paper sits here with the boxes it was read from.</p><a class="btn sm" href="matter.html#KF-1042">Open Kalra Fabricators</a>') + '</div></section></div>';
    } else if (mTab === 'hearings') {
      var hs = (m.hearings || []);
      P.innerHTML = '<section class="panel"><div class="panel-h"><h2>Hearings</h2><span>' + (hs.length ? plural(hs.filter(function (h) { return /Adjourned|Not served/.test(h[2]); }).length, 'adjournment', 'adjournments') + ' so far' : 'none yet') + '</span></div><div class="panel-b">' +
        (hs.length || m.next ? '<ol class="tl">' + hs.map(function (h) { return '<li class="' + (/Adjourned|Not served/.test(h[2]) ? 'adj' : '') + '"><span class="d">' + dlong(h[0]) + '</span><b>' + esc(h[1]) + '</b><span class="o">' + esc(h[2]) + '</span></li>'; }).join('') + (m.next ? '<li class="next"><span class="d">' + dlong(m.next[0]) + ' · next</span><b>' + esc(m.next[1]) + '</b><span class="o">In ' + plural(E.daysBetween(TODAY, m.next[0]), 'day', 'days') + '</span></li>' : '') + '</ol>' : '<p class="small">The case is not in court yet. Hearings appear here once the complaint is filed.</p>') + '</div></section>';
    } else if (mTab === 'drafts') {
      var ds = m.drafts || [];
      P.innerHTML = '<section class="panel"><div class="panel-h"><h2>Drafts</h2><a class="btn sm" href="drafts.html#' + m.id + '">New draft</a></div><table class="dtable"><tbody>' + (ds.length ? ds.map(function (d) { return '<tr data-href="drafts.html#' + m.id + '"><td><b>' + esc(d.t) + '</b></td><td class="r"><span class="chip ' + (d.s === 'Approved' ? 'ok' : d.s === 'Awaiting approval' ? 'warn' : '') + '">' + esc(d.s) + '</span></td></tr>'; }).join('') : '<tr><td><p class="small">No drafts yet.</p></td></tr>') + '</tbody></table></section>';
    } else if (mTab === 'settle') {
      var st = m.settlement;
      P.innerHTML = '<div class="grid-2"><section class="panel"><div class="panel-h"><h2>Compounding cost</h2><span>2025 Supreme Court stages</span></div><div class="panel-b" data-settle-box></div></section><section class="panel"><div class="panel-h"><h2>Settlement</h2></div><div class="panel-b">' +
        (st ? '<p class="h-s">' + inr(st.total) + ' in ' + plural(st.parts, 'instalment', 'instalments') + '</p><div class="bars" style="margin-top:14px"><i style="width:' + (st.paid / st.parts * 100) + '%;background:var(--green)"></i></div><p class="small" style="margin-top:8px">' + st.paid + ' of ' + st.parts + ' paid · ' + inr(st.total * st.paid / st.parts) + ' received</p>' : '<p class="small">No settlement on record. If the accused offers to pay, record the terms here and Tarikh will track each instalment against the hearings.</p>') + '</div></section></div>';
      var sb = P.querySelector('[data-settle-box]');
      sb.innerHTML = '<div class="calc" data-settle style="grid-template-columns:minmax(0,1fr)"><div class="field"><label for="st-amt">Cheque amount (₹)</label><input class="inp" id="st-amt" name="amount" inputmode="numeric" value="' + m.amount + '"></div><fieldset class="seg" style="border:0;margin:0;padding:0"><legend style="font-size:13px;font-weight:700;margin-bottom:8px">When the accused pays</legend>' + [['0', 'Before defence evidence', '0%'], ['5', 'After defence evidence, before judgment', '5%'], ['7.5', 'In revision or appeal', '7.5%'], ['10', 'Before the Supreme Court', '10%']].map(function (o, i) { return '<label><input type="radio" name="stage" value="' + o[0] + '"' + (i === 0 ? ' checked' : '') + '><span>' + o[1] + '</span><em>' + o[2] + '</em></label>'; }).join('') + '</fieldset><div class="out" aria-live="polite"><div class="k">Compounding cost</div><div class="v red" data-o="cost"></div><p data-o="note"></p><hr><div class="k">Total to pay</div><div class="v" data-o="total" style="font-size:36px"></div></div></div>';
      var root = sb.querySelector('[data-settle]'), amt = root.querySelector('input[name=amount]'), out = root.querySelector('.out');
      function upd() { var a = +String(amt.value).replace(/[^0-9]/g, '') || 0, r = root.querySelector('input[name=stage]:checked'), p = r ? +r.value : 0, c = Math.round(a * p / 100); out.querySelector('[data-o=cost]').textContent = inr(c); out.querySelector('[data-o=total]').textContent = inr(a + c); out.querySelector('[data-o=note]').textContent = p === 0 ? 'Paid before defence evidence: compounding with no cost.' : p + ' percent of the cheque amount, as the court directs.'; }
      amt.addEventListener('input', upd); root.querySelectorAll('input[name=stage]').forEach(function (r) { r.addEventListener('change', upd); }); upd();
    } else {
      P.innerHTML = '<section class="panel"><div class="panel-h"><h2>Activity</h2><span>append-only</span></div><table class="dtable"><tbody>' + activity(m).map(function (a) { return '<tr style="cursor:default"><td><b>' + esc(a[0]) + '</b><span class="s">' + esc(a[1]) + '</span></td></tr>'; }).join('') + '</tbody></table></section>';
    }
  }

  /* ---------- Diary ---------- */
  var dMonth = [2026, 10];
  function diary() {
    var y = dMonth[0], mo = dMonth[1], ev = T.eventsFor(D.MATTERS);
    var agenda = Object.keys(ev).filter(function (d) { return E.daysBetween(TODAY, d) >= 0; }).sort().slice(0, 12);
    C.innerHTML = '<div class="mhead"><div><h1>' + T.MONTH[mo] + ' ' + y + '</h1><p class="sub">Black for hearings, red for statutory deadlines, grey when a window opens. Sundays in red.</p></div>' +
      '<div class="acts"><button class="btn sm" id="dprev" aria-label="Previous month">←</button><button class="btn sm" id="dtoday">Today</button><button class="btn sm" id="dnext" aria-label="Next month">→</button></div></div>' +
      '<div class="grid-2 wide" style="margin-top:22px"><section class="panel"><div class="panel-b">' + T.monthHTML(y, mo, ev, 'matter.html') + '</div></section>' +
      '<section class="panel"><div class="panel-h"><h2>Coming up</h2></div><div class="panel-b"><ol class="tl">' + agenda.map(function (d) { return ev[d].map(function (e) { return '<li class="' + (e.cls === 'dl' ? 'next' : '') + '"><span class="d">' + T.WD[T.dow(d)].slice(0, 3) + ' ' + dshort(d) + '</span><b><a href="matter.html#' + e.id + '" style="text-decoration:none">' + esc(e.t) + '</a></b></li>'; }).join(''); }).join('') + '</ol></div></section></div>';
    function go(k) { var d = new Date(Date.UTC(dMonth[0], dMonth[1] + k, 1)); dMonth = [d.getUTCFullYear(), d.getUTCMonth()]; diary(); }
    doc.getElementById('dprev').addEventListener('click', function () { go(-1); });
    doc.getElementById('dnext').addEventListener('click', function () { go(1); });
    doc.getElementById('dtoday').addEventListener('click', function () { dMonth = [2026, 10]; diary(); });
  }

  /* ---------- Portfolio (Recover) ---------- */
  var pf = { stage: 'all', adv: 'all', sel: {} };
  var SC = { notice: '#E2321B', payment: '#F08A78', file: '#B92410', cognizance: '#C77C00', summons: '#E2A73B', evidence: '#0B0B0B', arguments: '#5A5A55', settled: '#17804A', decided: '#C2C2BD' };
  function portfolio() {
    var P = D.PORTFOLIO, total = 0, rec = 0, filed = P.filter(function (r) { return r.filed; }), adjs = 0;
    P.forEach(function (r) { total += r.amount; rec += r.recovered; }); filed.forEach(function (r) { adjs += r.adjournments; });
    var openW = P.filter(function (r) { return r.stage === 'file'; }).length, un = P.filter(function (r) { return !r.advocate; }).length;
    var counts = {}; D.STAGES.forEach(function (s) { counts[s.k] = 0; }); P.forEach(function (r) { counts[r.stage]++; });
    var age = [['Under 6 months', 0, 182], ['6 to 12 months', 183, 365], ['1 to 2 years', 366, 730], ['Over 2 years', 731, 1e6]].map(function (b) { return [b[0], filed.filter(function (r) { var a = E.daysBetween(r.filed, TODAY); return a >= b[1] && a <= b[2]; }).length]; });
    var rows = P.filter(function (r) { return (pf.stage === 'all' || r.stage === pf.stage) && (pf.adv === 'all' || (pf.adv === 'none' ? !r.advocate : r.advocate === pf.adv)); });
    var nsel = Object.keys(pf.sel).filter(function (k) { return pf.sel[k]; }).length;
    function rowStatus(r) {
      if (r.stage === 'notice' || r.stage === 'payment' || r.stage === 'file') return T.statusOf({ cheque: r.cheque, presented: r.presented, memo: r.memo, sent: r.sent, delivered: r.delivered, stage: r.stage });
      if (r.stage === 'settled') return { cls: 'ok', text: 'Settled' };
      if (r.stage === 'decided') return { cls: 'gone', text: 'Decided' };
      return { cls: '', text: T.STAGE_LABEL[r.stage] };
    }
    C.innerHTML = '<div class="mhead"><div><p class="tiny" style="font-family:var(--mono)">TARIKH RECOVER</p><h1 style="margin-top:8px">Northline Finance</h1><p class="sub">Sample lender. 64 bounced cheques across 8 courts and 4 panel advocates.</p></div><div class="acts"><button class="btn sm" id="imp">Import a return file</button><button class="btn sm solid" id="exp">Export for committee</button></div></div>' +
      '<div class="kpis six" style="margin-top:24px">' +
      [['Matters', P.length, ''], ['At stake', D.lakh(total), ''], ['Recovered', D.lakh(rec), ''], ['Windows open', openW, 'hot'], ['Adjournments per filed case', (adjs / filed.length).toFixed(1), ''], ['Unassigned', un, '']].map(function (k) { return '<div class="kpi ' + k[2] + '"><div class="k">' + k[0] + '</div><div class="v" style="font-size:26px">' + k[1] + '</div></div>'; }).join('') + '</div>' +
      '<div class="grid-2" style="margin-top:16px"><section class="panel"><div class="panel-h"><h2>By stage</h2><span>share of matters</span></div><div class="panel-b"><div class="bars" role="img" aria-label="' + D.STAGES.map(function (s) { return s.label + ' ' + counts[s.k]; }).join(', ') + '">' + D.STAGES.map(function (s) { return '<i style="width:' + (counts[s.k] / P.length * 100) + '%;background:' + SC[s.k] + '" title="' + s.label + ': ' + counts[s.k] + '"></i>'; }).join('') + '</div><div class="legend2">' + D.STAGES.map(function (s) { return '<span><i style="background:' + SC[s.k] + '"></i>' + s.label + ' ' + counts[s.k] + '</span>'; }).join('') + '</div></div></section>' +
      '<section class="panel"><div class="panel-h"><h2>Age of filed cases</h2><span>since filing</span></div><div class="panel-b stack" style="gap:10px">' + age.map(function (a) { return '<div style="display:grid;grid-template-columns:120px 1fr 28px;gap:10px;align-items:center;font-size:13px"><span>' + a[0] + '</span><div class="bars" style="height:10px"><i style="width:' + (a[1] / filed.length * 100) + '%;background:' + (a[0] === 'Over 2 years' ? 'var(--red)' : 'var(--bk)') + '"></i></div><b style="text-align:right">' + a[1] + '</b></div>'; }).join('') + '</div></section></div>' +
      '<div class="filters" style="margin:22px 0 14px"><label class="small" for="fs">Stage</label><select class="sel sm" id="fs"><option value="all">All stages</option>' + D.STAGES.map(function (s) { return '<option value="' + s.k + '"' + (pf.stage === s.k ? ' selected' : '') + '>' + s.label + ' (' + counts[s.k] + ')</option>'; }).join('') + '</select>' +
      '<label class="small" for="fa">Advocate</label><select class="sel sm" id="fa"><option value="all">Everyone</option><option value="none"' + (pf.adv === 'none' ? ' selected' : '') + '>Unassigned</option>' + D.PANEL.map(function (a) { return '<option' + (pf.adv === a ? ' selected' : '') + '>' + a + '</option>'; }).join('') + '</select><span class="small">' + rows.length + ' shown</span></div>' +
      '<section class="panel scroll"><div class="bulk"' + (nsel ? '' : ' hidden') + '><b>' + nsel + ' selected</b><label class="sr" for="ba">Assign to</label><select class="sel sm" id="ba">' + D.PANEL.map(function (a) { return '<option>' + a + '</option>'; }).join('') + '</select><button class="btn sm red" id="bgo">Assign</button><button class="btn sm" id="bclr" style="color:#fff">Clear</button></div>' +
      '<table class="dtable"><thead><tr><th scope="col"><input type="checkbox" id="sall" aria-label="Select all shown"' + (rows.length && rows.every(function (r) { return pf.sel[r.id]; }) ? ' checked' : '') + '></th><th scope="col">Borrower</th><th scope="col" class="hide-sm">Court</th><th scope="col" class="r">Amount</th><th scope="col">Stage</th><th scope="col" class="hide-sm">Next</th><th scope="col" class="hide-sm">Advocate</th></tr></thead><tbody>' +
      rows.map(function (r) { var s = rowStatus(r); return '<tr data-id="' + r.id + '"><td><input type="checkbox" aria-label="Select ' + esc(r.accused) + '"' + (pf.sel[r.id] ? ' checked' : '') + '></td><td><b>' + esc(r.accused) + '</b><span class="s">' + r.id + (r.filed ? ' · filed ' + dshort(r.filed) + ' ' + r.filed.slice(0, 4) + ' · ' + plural(r.adjournments, 'adjournment', 'adjournments') : '') + '</span></td><td class="hide-sm">' + r.city + '</td><td class="r">' + inr(r.amount) + '</td><td>' + T.chip(s) + '</td><td class="hide-sm">' + (r.next ? dshort(r.next) : '<span class="s">–</span>') + '</td><td class="hide-sm">' + (r.advocate ? esc(r.advocate) : '<span class="chip warn plain">Unassigned</span>') + '</td></tr>'; }).join('') + '</tbody></table></section>' +
      '<p class="tiny" style="margin-top:12px">Northline Finance and every borrower here are fictional. Rows are generated for the demo.</p>' +
      '<dialog class="modal" id="impd" aria-labelledby="impt"><div class="panel-h"><h2 id="impt">Import a return file</h2><button class="btn sm" id="impx">Close</button></div><div class="panel-b stack"><p class="small">Tarikh maps your columns once and remembers them. This is a preview of a sample file; nothing is imported in the demo.</p><table class="dtable"><thead><tr><th>Your column</th><th>Tarikh field</th><th>Sample</th></tr></thead><tbody>' +
      [['LOAN_AC', 'Matter reference', 'NL-0045821'], ['CUST_NAME', 'Drawer', 'Sekhon Hardware'], ['CHQ_NO', 'Cheque number', '114502'], ['CHQ_DT', 'Date on the cheque', '02/11/2026'], ['CHQ_AMT', 'Amount', '1,45,000'], ['RTN_DT', 'Returned on', '12/11/2026'], ['RTN_REASON', 'Return reason', '01 Funds insufficient'], ['MEMO_RCVD', 'Memo received', '14/11/2026']].map(function (r) { return '<tr style="cursor:default"><td class="mono">' + r[0] + '</td><td><b>' + r[1] + '</b></td><td>' + r[2] + '</td></tr>'; }).join('') + '</tbody></table><p class="small">After import: one matter per row, clocks counted, notices queued for drafting, and each matter offered to the panel advocate for its court.</p></div></dialog>';
    doc.getElementById('fs').addEventListener('change', function (e) { pf.stage = e.target.value; portfolio(); });
    doc.getElementById('fa').addEventListener('change', function (e) { pf.adv = e.target.value; portfolio(); });
    C.querySelectorAll('tbody tr[data-id]').forEach(function (tr) { tr.addEventListener('click', function (e) { var id = tr.getAttribute('data-id'); if (e.target.type !== 'checkbox') { var cb = tr.querySelector('input'); cb.checked = !cb.checked; } pf.sel[id] = tr.querySelector('input').checked; portfolio(); }); });
    doc.getElementById('sall').addEventListener('change', function (e) { rows.forEach(function (r) { pf.sel[r.id] = e.target.checked; }); portfolio(); });
    var bgo = doc.getElementById('bgo');
    if (bgo) { bgo.addEventListener('click', function () { var a = doc.getElementById('ba').value, n = 0; P.forEach(function (r) { if (pf.sel[r.id]) { r.advocate = a; n++; } }); pf.sel = {}; portfolio(); toast(plural(n, 'matter', 'matters') + ' assigned to ' + a + '. Demo only, nothing saved.'); }); doc.getElementById('bclr').addEventListener('click', function () { pf.sel = {}; portfolio(); }); }
    var dlg = doc.getElementById('impd');
    doc.getElementById('imp').addEventListener('click', function () { dlg.showModal(); });
    doc.getElementById('impx').addEventListener('click', function () { dlg.close(); });
    doc.getElementById('exp').addEventListener('click', function () { toast('In the live product this exports the portfolio. The demo has no downloads.'); });
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
    var id = (location.hash || '#KF-1042').slice(1), m = D.find(id) || D.MATTERS[0];
    C.innerHTML = '<div class="mhead"><div><h1>Drafts</h1><p class="sub">Built only from facts with a source. Nothing leaves draft until an advocate approves it.</p></div><div class="field"><label for="dm">Matter</label><select class="sel sm" id="dm">' + D.MATTERS.map(function (x) { return '<option value="' + x.id + '"' + (x.id === m.id ? ' selected' : '') + '>' + esc(x.accused) + ' · ' + x.id + '</option>'; }).join('') + '</select></div></div>' +
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
      var found = (m.drafts = m.drafts || []).filter(function (d) { return d.t.indexOf(t.split(' ')[0]) === 0; })[0];
      if (found) found.s = 'Approved'; else m.drafts.push({ t: t, s: 'Approved' });
      (m.log = m.log || []).unshift(['Approved: ' + t, n]); setCounts();
      toast('Approved by ' + n + '. Recorded for this session; nothing filed or sent.');
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
  render();
})();
