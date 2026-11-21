/* Tarikh v2 site behaviour. No dependencies. Pages work without it; the live tools need it. */
(function () {
  'use strict';
  var E = window.TarikhEngine, D = window.TarikhData;
  var doc = document;
  doc.documentElement.classList.add('js');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var MONTH = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  var HMONTH = ['जनवरी','फ़रवरी','मार्च','अप्रैल','मई','जून','जुलाई','अगस्त','सितंबर','अक्टूबर','नवंबर','दिसंबर'];
  var WD = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  var HWD = ['रविवार','सोमवार','मंगलवार','बुधवार','गुरुवार','शुक्रवार','शनिवार'];
  function dow(iso) { return new Date(iso + 'T00:00:00Z').getUTCDay(); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function plural(k, one, many) { return k + ' ' + (k === 1 ? one : many); }
  function dshort(iso) { return +iso.slice(8) + ' ' + MON[+iso.slice(5, 7) - 1]; }
  function dlong(iso) { return +iso.slice(8) + ' ' + MONTH[+iso.slice(5, 7) - 1] + ' ' + iso.slice(0, 4); }

  /* ---------- Calendar leaf ---------- */
  function leafHTML(iso, label, right) {
    var d = dow(iso), mi = +iso.slice(5, 7) - 1;
    return '<div class="leaf' + (d === 0 ? ' sun' : '') + '" role="img" aria-label="' + esc(label + ': ' + WD[d] + ', ' + dlong(iso)) + '">' +
      '<div class="holes" aria-hidden="true"><i></i><i></i></div>' +
      '<div class="lh"><b>' + MONTH[mi] + ' ' + iso.slice(0, 4) + '</b><span lang="hi">' + HMONTH[mi] + '</span></div>' +
      '<div class="ld"><div class="n">' + (+iso.slice(8)) + '</div><div class="wd">' + WD[d] + '</div><div class="wdh" lang="hi">' + HWD[d] + '</div></div>' +
      '<div class="lf"><b>' + esc(label) + '</b><span>' + esc(right || '') + '</span></div></div>';
  }

  /* ---------- Matter status: computed from dates, never stored ---------- */
  var STAGE_LABEL = {}; (D ? D.STAGES : []).forEach(function (s) { STAGE_LABEL[s.k] = s.label; });
  function windowsOf(m, today) { return E.computeWindows({ cheque: m.cheque, presented: m.presented, memo: m.memo, sent: m.sent, delivered: m.delivered, today: today || D.TODAY }); }
  function statusOf(m, today) {
    today = today || D.TODAY;
    var w = windowsOf(m, today), c = w.complaint, n = w.notice, r;
    if (m.stage === 'settled') r = { cls: 'ok', text: 'Settled', key: null, keyLabel: 'Settled', rank: 9e6 };
    else if (m.stage === 'decided') r = { cls: 'gone', text: 'Decided', key: null, keyLabel: 'Decided', rank: 9e6 + 1 };
    else if (m.filed) r = { cls: 'calm', text: STAGE_LABEL[m.stage] || 'In court', key: m.next ? m.next[0] : null, keyLabel: m.next ? m.next[1] : 'No date fixed', rank: m.next ? 1e5 + E.daysBetween(today, m.next[0]) : 8e6 };
    else if (!m.memo) r = { cls: 'warn', text: 'Date needed', key: null, keyLabel: 'Memo received date missing', rank: 0 };
    else if (!m.sent) { var nl = E.daysBetween(today, n.closes); r = nl < 0 ? { cls: 'gone', text: 'Notice time over', key: n.closes, keyLabel: 'Notice was due', rank: 7e6 } : { cls: nl <= 7 ? 'hot' : nl <= 14 ? 'warn' : 'calm', text: 'Notice due in ' + plural(nl, 'day', 'days'), key: n.closes, keyLabel: 'Last day to send notice', rank: nl }; }
    else if (!m.delivered) r = { cls: 'warn', text: 'Delivery date needed', key: null, keyLabel: 'Notice delivery date missing', rank: 1 };
    else if (c.status === 'upcoming') r = { cls: 'calm', text: 'Opens in ' + plural(E.daysBetween(today, c.opens), 'day', 'days'), key: c.opens, keyLabel: 'Complaint window opens', rank: 50 + E.daysBetween(today, c.opens) };
    else if (c.status === 'expired') r = { cls: 'gone', text: 'Closed ' + plural(E.daysBetween(c.closes, today), 'day', 'days') + ' ago', key: c.closes, keyLabel: 'Window closed', rank: 6e6 };
    else r = { cls: c.daysLeft <= 7 ? 'hot' : c.daysLeft <= 21 ? 'warn' : 'calm', text: plural(c.daysLeft, 'day', 'days') + ' to file', key: c.closes, keyLabel: 'Last day to file', rank: c.daysLeft };
    r.windows = w; return r;
  }
  function chip(st) { return '<span class="chip ' + st.cls + '">' + esc(st.text) + '</span>'; }

  /* ---------- Header: menu and mega menus ---------- */
  var hdr = doc.querySelector('.hdr'), mb = doc.querySelector('.menu-btn');
  if (hdr && mb) mb.addEventListener('click', function () { var o = hdr.classList.toggle('open'); mb.setAttribute('aria-expanded', String(o)); mb.textContent = o ? 'Close' : 'Menu'; });
  var dds = doc.querySelectorAll('.dd');
  function syncScrim() { doc.body.classList.toggle('menu-open', !!doc.querySelector('.dd.open') && window.innerWidth > 1000); }
  function closeAll(except) { dds.forEach(function (d) { if (d !== except) { d.classList.remove('open'); var b = d.querySelector('button'); if (b) b.setAttribute('aria-expanded', 'false'); } }); syncScrim(); }
  if (hdr) { var onScroll = function () { hdr.classList.toggle('scrolled', window.scrollY > 24); }; window.addEventListener('scroll', onScroll, { passive: true }); onScroll(); }
  var fine = window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches, hoverT;
  if (fine) dds.forEach(function (d) {
    d.addEventListener('mouseenter', function () { clearTimeout(hoverT); hoverT = setTimeout(function () { closeAll(d); d.classList.add('open'); d.querySelector('button').setAttribute('aria-expanded', 'true'); syncScrim(); }, 90); });
    d.addEventListener('mouseleave', function () { clearTimeout(hoverT); hoverT = setTimeout(function () { closeAll(); }, 160); });
  });
  dds.forEach(function (d) {
    var b = d.querySelector('button');
    b.addEventListener('click', function (e) { e.stopPropagation(); var o = !d.classList.contains('open'); closeAll(d); d.classList.toggle('open', o); b.setAttribute('aria-expanded', String(o)); syncScrim(); });
  });
  doc.addEventListener('click', function (e) { if (!e.target.closest('.dd')) closeAll(); });
  doc.addEventListener('keydown', function (e) { if (e.key === 'Escape') { closeAll(); if (hdr && hdr.classList.contains('open')) mb.click(); } });

  /* ---------- Reveal and count-up ---------- */
  function fmtCount(n, f) { return f === 'in' ? D.inr(n).slice(1) : String(n); }
  function count(el) {
    var to = +el.getAttribute('data-count'), f = el.getAttribute('data-format'), t0 = null, dur = 1400;
    if (reduce) { el.textContent = fmtCount(to, f); return; }
    function step(t) { if (!t0) t0 = t; var p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3); el.textContent = fmtCount(Math.round(to * e), f); if (p < 1) requestAnimationFrame(step); }
    requestAnimationFrame(step);
  }
  var targets = doc.querySelectorAll('.rise,[data-count]');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) { es.forEach(function (en) { if (en.isIntersecting) { var t = en.target; if (t.hasAttribute('data-count')) count(t); else t.classList.add('in'); io.unobserve(t); } }); }, { rootMargin: '0px 0px -6% 0px' });
    targets.forEach(function (t) { io.observe(t); });
  } else targets.forEach(function (t) { t.classList.add('in'); });

  /* ---------- Tear-off pad: cycles through a matter's key dates ---------- */
  doc.querySelectorAll('[data-pad]').forEach(function (pad) {
    var items = JSON.parse(pad.getAttribute('data-pad')), i = 0, timer = null;
    function render() {
      var a = items[i], b = items[(i + 1) % items.length];
      pad.innerHTML = '<div class="base-wrap">' + leafHTML(b[0], b[1], b[2]).replace('class="leaf', 'class="leaf base') + '</div>' + leafHTML(a[0], a[1], a[2]);
      var top = pad.lastElementChild; top.style.position = 'absolute'; top.style.left = '0'; top.style.top = '0'; top.style.zIndex = '2';
    }
    function next() {
      var top = pad.lastElementChild; if (reduce) { i = (i + 1) % items.length; render(); return; }
      top.classList.add('tear'); setTimeout(function () { i = (i + 1) % items.length; render(); }, 760);
    }
    render();
    pad.setAttribute('tabindex', '0'); pad.setAttribute('role', 'button'); pad.setAttribute('aria-label', 'Tear off the top leaf to see the next date');
    pad.addEventListener('click', next);
    pad.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); next(); } });
    if (!reduce && pad.hasAttribute('data-auto')) {
      timer = setInterval(next, 3600);
      pad.addEventListener('mouseenter', function () { clearInterval(timer); });
    }
  });

  /* ---------- Tabs (audience switcher and app tabs) ---------- */
  doc.querySelectorAll('[role=tablist]').forEach(function (tl) {
    var tabs = Array.prototype.slice.call(tl.querySelectorAll('[role=tab]'));
    function sel(t, focus) {
      tabs.forEach(function (x) { var on = x === t; x.setAttribute('aria-selected', String(on)); x.tabIndex = on ? 0 : -1; var p = doc.getElementById(x.getAttribute('aria-controls')); if (p) p.hidden = !on; });
      if (focus) t.focus();
    }
    tabs.forEach(function (t, k) {
      t.addEventListener('click', function () { sel(t); });
      t.addEventListener('keydown', function (e) { var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0; if (d) { e.preventDefault(); sel(tabs[(k + d + tabs.length) % tabs.length], true); } });
    });
  });

  /* ---------- The long table ---------- */
  var SPAN = 144;       // days drawn: cheque date plus 144
  var PIN_MAX = 92;     // the four event pins stop here so every clock still fits on the axis
  var ORDER = ['p', 'm', 'n', 'd'];

  function el(tag, cls, text) {
    var n = doc.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function pc(n) { return (n / SPAN * 100).toFixed(3) + '%'; }
  function plural(k, one, many) { return k + ' ' + (k === 1 ? one : many); }

  function mountLongTable(root) {
    var base = root.getAttribute('data-cheque') || '2026-09-20';
    var real = {
      p: E.daysBetween(base, root.getAttribute('data-presented') || '2026-10-01'),
      m: E.daysBetween(base, root.getAttribute('data-memo') || '2026-10-05'),
      n: E.daysBetween(base, root.getAttribute('data-sent') || '2026-10-30'),
      d: E.daysBetween(base, root.getAttribute('data-delivered') || '2026-11-03'),
      t: E.daysBetween(base, root.getAttribute('data-today') || '2026-11-20')
    };
    var state = { p: real.p, m: real.m, n: real.n, d: real.d, t: real.t };
    var iso = function (n) { return E.addDays(base, n); };
    var heading = root.getAttribute('data-heading') || 'Move the dates';
    var sub = root.getAttribute('data-sub') || 'Move any pin. The four clocks follow. Nothing is saved: it is a way to ask what if the notice had gone out later.';

    root.classList.add('lt');
    root.innerHTML = '';

    // Result: date, sentence, stamp.
    var top = el('div', 'lt-top');
    var date = el('div', 'lt-date');
    date.appendChild(el('div', 'l', 'Last day to file the complaint'));
    var big = el('div', 'big'); date.appendChild(big);
    var yr = el('div', 'yr'); date.appendChild(yr);
    var note = el('p', 'note'); note.setAttribute('aria-live', 'polite'); date.appendChild(note);
    var safe = el('p', 'safe'); date.appendChild(safe);
    top.appendChild(date);

    var stampWrap = el('div', 'lt-stamp');
    stampWrap.innerHTML =
      '<svg viewBox="0 0 172 172" fill="none" role="img" aria-label="Days left">' +
      '<circle cx="86" cy="86" r="82" stroke="currentColor" stroke-width="3"/>' +
      '<circle cx="86" cy="86" r="74" stroke="currentColor" stroke-width="1"/>' +
      '<text class="s-num" x="86" y="114" text-anchor="middle" font-family="Anton, sans-serif" font-size="62" font-weight="400" fill="currentColor"></text>' +
      '<text class="s-word" x="86" y="138" text-anchor="middle" font-family="Schibsted Grotesk, sans-serif" font-size="11" font-weight="700" letter-spacing="2.4" fill="currentColor"></text>' +
      '<path d="M42 58h88" stroke="currentColor" stroke-width="1"/>' +
      '<text x="86" y="48" text-anchor="middle" font-family="Schibsted Grotesk, sans-serif" font-size="9" font-weight="700" letter-spacing="2.2" fill="currentColor">COMPLAINT</text>' +
      '</svg>';
    var pill = el('span', 'pill'); stampWrap.appendChild(pill);
    stampWrap.style.color = 'var(--ramp)';
    top.appendChild(stampWrap);
    root.appendChild(top);

    // Board.
    var board = el('div', 'lt-board');
    var head = el('div', 'lt-head');
    var hd = el('div');
    hd.appendChild(el('h3', 'd3', heading));
    var hp = el('p', 't-sm', sub); hp.style.marginTop = '6px'; hp.style.maxWidth = '540px'; hd.appendChild(hp);
    head.appendChild(hd);
    var reset = el('button', 'btn sm', 'Back to the real dates'); reset.type = 'button';
    head.appendChild(reset);
    board.appendChild(head);

    var plot = el('div', 'lt-plot');
    var names = el('div', 'lt-names'); names.appendChild(el('div', 'sp'));
    var laneDefs = [
      ['Cheque presented in time', 'Three months from the date on it'],
      ['Demand notice', '30 days from receiving the memo'],
      ['Drawer’s time to pay', '15 days from the day after receipt. Their clock'],
      ['Complaint to the Magistrate', 'One month from the day payment fell due']
    ];
    laneDefs.forEach(function (d) {
      var n = el('div'); n.appendChild(el('b', null, d[0])); n.appendChild(el('span', null, d[1])); names.appendChild(n);
    });
    plot.appendChild(names);

    var area = el('div', 'lt-area');
    var axis = el('div', 'lt-axis'); axis.setAttribute('aria-hidden', 'true');
    for (var wk = 0; wk <= SPAN; wk += 7) { var t = el('div', 't'); t.style.left = pc(wk); axis.appendChild(t); }
    var firstOfMonth = [];
    for (var k = 1; k <= SPAN; k++) { if (E.addDays(base, k).slice(8) === '01') firstOfMonth.push(k); }
    var tl0 = el('div', 'tl first', E.short(base)); tl0.style.left = '0'; axis.appendChild(tl0);
    firstOfMonth.forEach(function (k, idx) {
      var tt = el('div', 't m'); tt.style.left = pc(k); axis.appendChild(tt);
      var d = iso(k); var lab = el('div', 'tl' + (idx % 2 ? ' hide-sm' : ''), '1 ' + E.MON[+d.slice(5, 7) - 1] + (d.slice(5, 7) === '01' ? ' ' + d.slice(0, 4) : ''));
      lab.style.left = pc(k); axis.appendChild(lab);
    });
    area.appendChild(axis);

    var lanes = el('div', 'lt-lanes');
    var laneEls = laneDefs.map(function (d) {
      var l = el('div', 'lane'); l.setAttribute('data-name', d[0]);
      var bar = el('div', 'bar'); var cap = el('div', 'lcap');
      l.appendChild(bar); l.appendChild(cap); lanes.appendChild(l);
      return { bar: bar, cap: cap };
    });
    var pinDefs = [
      { k: 'p', name: 'Presented', aria: 'Date the cheque was presented', level: 0 },
      { k: 'm', name: 'Memo received', aria: 'Date the return memo was received', level: 1 },
      { k: 'n', name: 'Notice sent', aria: 'Date the demand notice was sent', level: 0 },
      { k: 'd', name: 'Notice delivered', aria: 'Date the drawer received the notice', level: 1 },
      { k: 't', name: 'Today', aria: 'Today, for what-if checks', level: 0, cls: 'today' }
    ];
    var guides = pinDefs.map(function (p) {
      var g = el('div', 'gl' + (p.k === 't' ? ' today' : '')); lanes.appendChild(g);
      var tag = null;
      if (p.k === 't') { tag = el('span', 'tag'); g.appendChild(tag); }
      return { g: g, tag: tag };
    });
    area.appendChild(lanes);

    var rail = el('div', 'lt-rail');
    var inputs = [], labels = [];
    pinDefs.forEach(function (p) {
      var inp = el('input', 'rng' + (p.cls ? ' ' + p.cls : ''));
      inp.type = 'range'; inp.min = '0'; inp.max = String(SPAN); inp.step = '1';
      inp.setAttribute('aria-label', p.aria);
      inp.addEventListener('input', function () { move(p.k, parseInt(inp.value, 10)); });
      rail.appendChild(inp); inputs.push(inp);
    });
    pinDefs.forEach(function (p) {
      var l = el('div', 'pl'); l.style.top = (60 + p.level * 40) + 'px';
      var b = el('b', null, p.name); var s = el('span'); l.appendChild(b); l.appendChild(s);
      rail.appendChild(l); labels.push({ box: l, span: s });
    });
    area.appendChild(rail);
    plot.appendChild(area);
    board.appendChild(plot);

    var legend = el('dl', 'lt-legend');
    var legendVals = pinDefs.map(function (p) {
      var row = el('div'); row.appendChild(el('dt', null, p.name)); var dd = el('dd'); row.appendChild(dd); legend.appendChild(row); return dd;
    });
    board.appendChild(legend);
    root.appendChild(board);

    function move(key, value) {
      if (key !== 't') value = Math.min(value, PIN_MAX);
      state[key] = value;
      var i = ORDER.indexOf(key);
      if (i >= 0) {
        for (var j = i + 1; j < ORDER.length; j++) state[ORDER[j]] = Math.max(state[ORDER[j]], value);
        for (var j2 = 0; j2 < i; j2++) state[ORDER[j2]] = Math.min(state[ORDER[j2]], value);
      }
      update();
    }
    reset.addEventListener('click', function () { state = { p: real.p, m: real.m, n: real.n, d: real.d, t: real.t }; update(); });

    function bar(a, b, fill, edge, cls) {
      return { left: pc(a), width: (((b - a + 1) / SPAN) * 100).toFixed(3) + '%', fill: fill, edge: edge, cls: cls || '' };
    }

    function update() {
      var w = E.computeWindows({ cheque: base, presented: iso(state.p), memo: iso(state.m), sent: iso(state.n), delivered: iso(state.d), today: iso(state.t) });
      var cOpen = E.daysBetween(base, w.complaint.opens), cEnd = E.daysBetween(base, w.complaint.closes);
      var nOpen = E.daysBetween(base, w.notice.opens), nEnd = E.daysBetween(base, w.notice.closes);
      var pOpen = E.daysBetween(base, w.payment.opens), pEnd = E.daysBetween(base, w.payment.closes);
      var vEnd = E.daysBetween(base, w.validity.closes);
      var today = state.t;
      var waiting = w.complaint.status === 'upcoming', ended = w.complaint.status === 'expired';
      var left = w.complaint.daysLeft;
      var noticeLate = w.notice.status === 'expired', presentedLate = w.validity.status === 'expired';

      var ramp = 'calm';
      if (ended) ramp = 'gone'; else if (!waiting && left <= 7) ramp = 'hot'; else if (!waiting && left <= 21) ramp = 'warn';
      root.setAttribute('data-ramp', ramp);

      var last = w.complaint.closes;
      var wd = E.weekday(last);
      big.textContent = last.slice(8).replace(/^0/, '') + ' ' + E.MONTH[+last.slice(5, 7) - 1];
      yr.textContent = last.slice(0, 4) + ', ' + (wd === 'Saturday' || wd === 'Sunday' ? 'a ' : 'a ') + wd;

      var text;
      if (presentedLate) text = 'The cheque was presented after its three months ran out. The advocate decides what follows.';
      else if (noticeLate) text = 'The notice went out ' + plural(state.n - nEnd, 'day', 'days') + ' after its 30 days closed. The advocate decides what that means for the complaint.';
      else if (waiting) text = 'The drawer still has ' + plural(cOpen - today, 'day', 'days') + ' to pay. The complaint window opens on ' + E.short(w.complaint.opens) + '.';
      else if (ended) text = 'The window closed ' + plural(today - cEnd, 'day', 'days') + ' ago. Whether a late complaint can be excused is for the advocate.';
      else text = 'Counted from ' + E.short(w.complaint.opens) + ', the day after the drawer’s 15 days ended.' + ((wd === 'Saturday' || wd === 'Sunday') ? ' ' + wd + ' may not be a court day, so confirm the court sits.' : '');
      note.textContent = text;
      safe.textContent = (w.complaint.conservativeCloses !== w.complaint.closes && !ended)
        ? 'Counting from the day payment fell due gives ' + E.short(w.complaint.conservativeCloses) + '. Filing by then leaves no doubt.' : '';

      var num, word, pt;
      if (waiting) { num = String(cOpen - today); word = 'DAYS TO OPEN'; pt = 'Opens in ' + plural(cOpen - today, 'day', 'days'); }
      else if (ended) { num = String(today - cEnd); word = 'DAYS AGO'; pt = 'Ended ' + plural(today - cEnd, 'day', 'days') + ' ago'; }
      else { num = String(left); word = left === 1 ? 'DAY LEFT' : 'DAYS LEFT'; pt = plural(left, 'day', 'days') + ' left'; }
      var sn = stampWrap.querySelector('.s-num'); sn.textContent = num; sn.setAttribute('font-size', num.length > 2 ? '52' : '62');
      stampWrap.querySelector('.s-word').textContent = word;
      stampWrap.querySelector('svg').setAttribute('aria-label', pt);
      pill.textContent = pt;

      // Lanes
      var b1 = bar(0, vEnd, 'var(--rule)', 'transparent');
      var b2 = bar(nOpen, nEnd, noticeLate ? 'var(--hot)' : 'var(--ink-3)', 'transparent');
      var b3 = bar(pOpen, pEnd, 'transparent', 'var(--ink-3)', 'theirs');
      var b4 = bar(cOpen, cEnd, waiting ? 'transparent' : 'var(--ramp)', waiting ? 'var(--calm)' : 'transparent');
      var bars = [b1, b2, b3, b4];
      var caps = [
        [presentedLate ? 'Presented ' + E.short(iso(state.p)) + ', after validity' : 'Presented ' + E.short(iso(state.p)) + ', in time', Math.min(state.p + 2, 80), presentedLate ? 'var(--hot)' : 'var(--ink-2)'],
        [noticeLate ? 'Sent ' + E.short(iso(state.n)) + ', ' + plural(state.n - nEnd, 'day', 'days') + ' late' : 'Sent ' + E.short(iso(state.n)) + ', ' + plural(nEnd - state.n, 'day', 'days') + ' to spare', nOpen, noticeLate ? 'var(--hot)' : 'var(--ink-2)'],
        [(today > pEnd ? E.short(w.payment.opens) + ' to ' + E.short(w.payment.closes) + ', unpaid' : E.short(w.payment.opens) + ' to ' + E.short(w.payment.closes)), pOpen, 'var(--ink-2)'],
        [E.short(w.complaint.opens) + ' to ' + E.short(w.complaint.closes) + (ended ? ', ended' : waiting ? ', not open yet' : ', open'), cOpen, 'var(--ramp)']
      ];
      laneEls.forEach(function (l, i) {
        var b = bars[i];
        l.bar.className = 'bar' + (b.cls ? ' ' + b.cls : '');
        l.bar.style.left = b.left; l.bar.style.width = b.width; l.bar.style.background = b.fill; l.bar.style.borderColor = b.edge;
        l.cap.textContent = caps[i][0]; l.cap.style.left = pc(caps[i][1]); l.cap.style.color = caps[i][2];
      });

      // Pins
      pinDefs.forEach(function (p, i) {
        var v = state[p.k];
        inputs[i].value = String(v);
        inputs[i].setAttribute('aria-valuetext', E.long(iso(v)));
        guides[i].g.style.left = pc(v);
        labels[i].box.style.left = pc(v);
        labels[i].span.textContent = E.short(iso(v));
        labels[i].box.className = 'pl' + (v !== real[p.k] ? ' moved' : '');
        legendVals[i].textContent = E.long(iso(v)) + (v !== real[p.k] ? ' (moved from ' + E.short(iso(real[p.k])) + ')' : '');
      });
      guides[4].tag.textContent = 'Today ' + E.short(iso(state.t));
    }
    update();
    return { state: function () { return state; }, move: move, update: update };
  }


  doc.querySelectorAll('[data-longtable]').forEach(function (r) { r.__lt = mountLongTable(r); });

  /* ---------- Settle: compounding cost by stage (Sanjabij Tari, 2025) ---------- */
  doc.querySelectorAll('[data-settle]').forEach(function (root) {
    var amt = root.querySelector('input[name=amount]'), out = root.querySelector('.out');
    function upd() {
      var a = Math.max(0, +String(amt.value).replace(/[^0-9]/g, '') || 0);
      var r = root.querySelector('input[name=stage]:checked'), pct = r ? +r.value : 0;
      var cost = Math.round(a * pct / 100);
      out.querySelector('[data-o=cost]').textContent = D.inr(cost);
      out.querySelector('[data-o=total]').textContent = D.inr(a + cost);
      out.querySelector('[data-o=note]').textContent = pct === 0 ? 'Paid before defence evidence: compounding with no cost.' : pct + ' percent of the cheque amount, paid as costs where the court directs.';
    }
    amt.addEventListener('input', upd); root.querySelectorAll('input[name=stage]').forEach(function (r) { r.addEventListener('change', upd); });
    upd();
  });

  /* ---------- Mini Today window (hero) ---------- */
  doc.querySelectorAll('[data-mini-today]').forEach(function (el) {
    var ms = D.MATTERS.map(function (m) { return { m: m, s: statusOf(m) }; }).sort(function (a, b) { return a.s.rank - b.s.rank; });
    var closing = ms.filter(function (x) { return x.s.cls === 'hot'; }).length;
    var week = ms.filter(function (x) { return x.m.next && E.daysBetween(D.TODAY, x.m.next[0]) >= 0 && E.daysBetween(D.TODAY, x.m.next[0]) <= 7; });
    var drafts = 0; D.MATTERS.forEach(function (m) { (m.drafts || []).forEach(function (d) { if (d.s === 'Awaiting approval') drafts++; }); });
    var rows = ms.filter(function (x) { return !x.m.filed && x.s.key; }).slice(0, 5).map(function (x) {
      return '<div class="row"><div><b>' + esc(x.m.accused) + '</b><span>' + esc(x.m.complainant) + ' · ' + D.inr(x.m.amount) + '</span></div>' + chip(x.s) + '</div>';
    }).join('');
    var hear = week.map(function (x) { return '<div class="row"><div><b>' + esc(x.m.accused) + '</b><span>' + esc(x.m.next[1]) + '</span></div><div class="dt">' + (+x.m.next[0].slice(8)) + '<small>' + MON[+x.m.next[0].slice(5, 7) - 1].toUpperCase() + '</small></div></div>'; }).join('');
    el.innerHTML = '<div class="wh"><b>Today, ' + dlong(D.TODAY) + '</b><span class="tiny">' + esc(D.CHAMBERS.name) + ' · sample</span></div>' +
      '<div class="kpis"><div class="kpi"><div class="k">Open matters</div><div class="v">' + ms.filter(function (x) { return x.m.stage !== 'settled'; }).length + '</div></div>' +
      '<div class="kpi hot"><div class="k">Closing in 7 days</div><div class="v">' + closing + '</div></div>' +
      '<div class="kpi"><div class="k">Hearings this week</div><div class="v">' + week.length + '</div></div>' +
      '<div class="kpi"><div class="k">Drafts to approve</div><div class="v">' + drafts + '</div></div></div>' +
      '<div class="win-cols"><div class="list"><div class="lh">Deadlines, most urgent first<span>counted by rule</span></div>' + rows + '</div>' +
      '<div class="list"><div class="lh">Hearings this week<span>next tarikh</span></div>' + hear + '</div></div>';
  });

  /* ---------- Month grid (used by the site and the app) ---------- */
  function eventsFor(ms) {
    var ev = {};
    function put(d, o) { (ev[d] = ev[d] || []).push(o); }
    ms.forEach(function (m) {
      if (m.next) put(m.next[0], { cls: '', t: m.accused + ': ' + m.next[1], id: m.id });
      if (!m.filed && m.stage !== 'settled') { var s = statusOf(m); if (s.key && (s.cls === 'hot' || s.cls === 'warn' || s.cls === 'calm') && s.keyLabel !== 'Complaint window opens') put(s.key, { cls: 'dl', t: s.keyLabel + ': ' + m.accused, id: m.id }); if (s.keyLabel === 'Complaint window opens') put(s.key, { cls: 'soft', t: 'Window opens: ' + m.accused, id: m.id }); }
    });
    return ev;
  }
  function monthHTML(y, mo, ev, linkBase) {
    var first = new Date(Date.UTC(y, mo, 1)), start = new Date(first); start.setUTCDate(1 - first.getUTCDay());
    var h = '<table class="month"><caption class="sr">' + MONTH[mo] + ' ' + y + '</caption><thead><tr>' + ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(function (d) { return '<th scope="col">' + d + '</th>'; }).join('') + '</tr></thead><tbody>';
    for (var w = 0; w < 6; w++) {
      h += '<tr>';
      for (var k = 0; k < 7; k++) {
        var d = new Date(start); d.setUTCDate(start.getUTCDate() + w * 7 + k); var iso = d.toISOString().slice(0, 10), out = d.getUTCMonth() !== mo;
        var cls = (out ? 'out ' : '') + (k === 0 ? 'sun ' : '') + (iso === D.TODAY ? 'today' : '');
        h += '<td class="' + cls + '"><span class="d">' + d.getUTCDate() + '</span>';
        if (!out) (ev[iso] || []).slice(0, 3).forEach(function (e) { h += linkBase != null ? '<a class="ev ' + e.cls + '" href="' + linkBase + '#' + e.id + '" title="' + esc(e.t) + '">' + esc(e.t) + '</a>' : '<span class="ev ' + e.cls + '" title="' + esc(e.t) + '">' + esc(e.t) + '</span>'; });
        h += '</td>';
      }
      h += '</tr>';
      if (w >= 4) { var nd = new Date(start); nd.setUTCDate(start.getUTCDate() + (w + 1) * 7); if (nd.getUTCMonth() !== mo) break; }
    }
    return h + '</tbody></table>';
  }
  doc.querySelectorAll('[data-mini-month]').forEach(function (el) { var p = el.getAttribute('data-mini-month').split('-'); el.innerHTML = monthHTML(+p[0], +p[1] - 1, eventsFor(D.MATTERS), null); });

  /* ---------- Tarikh Check: the free deadline checker ---------- */
  var cf = doc.getElementById('check-form');
  if (cf) {
    var res = doc.getElementById('check-result');
    function v(id) { var x = doc.getElementById(id).value; return x || null; }
    function run(e) {
      if (e) e.preventDefault();
      var i = { cheque: v('ck-cheque'), presented: v('ck-presented'), memo: v('ck-memo'), sent: v('ck-sent'), delivered: v('ck-delivered'), today: v('ck-today') || D.TODAY };
      var err = doc.getElementById('ck-err');
      if (!i.memo) { err.textContent = 'Enter the date the return memo reached you. Every other date is counted from it.'; doc.getElementById('ck-memo').focus(); return; }
      err.textContent = '';
      var w = E.computeWindows(i), steps = [], lead, leafDate, leafLabel, tone = 'calm';
      if (i.cheque && i.presented && E.daysBetween(w.validity.closes, i.presented) > 0) steps.push(['hot', 'The cheque may have been presented after its three months.', 'Validity ran to ' + dlong(w.validity.closes) + '. Ask an advocate before you spend on a notice.']);
      if (!i.sent) {
        var nl = E.daysBetween(i.today, w.notice.closes);
        if (nl >= 0) { lead = 'Send the demand notice by ' + dlong(w.notice.closes) + '.'; leafDate = w.notice.closes; leafLabel = 'Last day to send notice'; tone = nl <= 7 ? 'hot' : 'calm';
          steps.push([tone, plural(nl, 'day', 'days') + ' left to send the notice.', 'Thirty days from the day the memo reached you. Send it by registered post with acknowledgement, and keep the receipt and tracking.']);
          steps.push(['calm', 'Write down the drawer’s email and phone now.', 'Since November 2025 courts ask for them, on affidavit, when the complaint is filed.']); }
        else { lead = 'The 30 days to send a notice ended on ' + dlong(w.notice.closes) + '.'; leafDate = w.notice.closes; leafLabel = 'Notice time ended'; tone = 'hot';
          steps.push(['hot', 'Speak to an advocate this week.', 'A late notice usually cannot start a valid complaint. A fresh presentation, if the cheque is still valid, or a civil suit may still be open to you.']); }
      } else if (!i.delivered) { lead = 'Find out when the drawer received the notice.'; tone = 'calm'; steps.push(['calm', 'The postal tracking or acknowledgement card gives the date.', 'The drawer’s 15 days, and then your complaint window, are counted from it.']); }
      else {
        var c = w.complaint;
        if (c.status === 'upcoming') { lead = 'Wait. The drawer can still pay until ' + dlong(w.payment.closes) + '.'; leafDate = c.opens; leafLabel = 'Complaint window opens'; steps.push(['calm', 'Your complaint window opens on ' + dlong(c.opens) + '.', 'A complaint filed before then is premature.']); steps.push(['calm', 'Last day to file: ' + dlong(c.closes) + '.', 'Counted under the General Clauses Act, as the Supreme Court did in Econ Antri (2013).']); }
        else if (c.status === 'expired') { lead = 'The one-month window closed on ' + dlong(c.closes) + '.'; leafDate = c.closes; leafLabel = 'Window closed'; tone = 'hot'; steps.push(['hot', 'A court can excuse delay if there is sufficient cause.', 'That is for an advocate to argue, with an application to condone the delay.']); }
        else { lead = 'File the complaint by ' + dlong(c.closes) + '.'; leafDate = c.closes; leafLabel = 'Last day to file'; tone = c.daysLeft <= 7 ? 'hot' : 'calm';
          steps.push([tone, plural(c.daysLeft, 'day', 'days') + ' left to file.', 'The window opened on ' + dlong(c.opens) + '. Filing by ' + dlong(c.conservativeCloses) + ' leaves no room for argument.']);
          if ([0, 6].indexOf(dow(c.closes)) >= 0) steps.push(['warn', 'The last day is a ' + WD[dow(c.closes)] + '.', 'Check whether the court sits that day. Do not plan to file on the last day.']);
          steps.push(['calm', 'Bring five papers to the advocate.', 'The cheque, the return memo, the notice, the postal receipt and tracking, and anything showing the debt.']); }
      }
      res.hidden = false;
      res.querySelector('[data-r=lead]').textContent = lead;
      res.querySelector('[data-r=leaf]').innerHTML = leafDate ? leafHTML(leafDate, leafLabel, '') : '';
      res.querySelector('[data-r=steps]').innerHTML = steps.map(function (s) { return '<li><span class="chip ' + s[0] + ' plain">' + (s[0] === 'hot' ? 'Act now' : s[0] === 'warn' ? 'Check' : 'Next') + '</span><div><b>' + esc(s[1]) + '</b><p class="small">' + esc(s[2]) + '</p></div></li>'; }).join('');
      res.querySelector('[data-r=table]').innerHTML = [['Cheque valid to', w.validity.closes], ['Notice by', w.notice.closes], ['Drawer may pay until', w.payment.closes], ['Complaint window', w.complaint.opens ? dshort(w.complaint.opens) + ' to ' + dlong(w.complaint.closes) : null]].map(function (r) { return '<tr><td>' + r[0] + '</td><td class="v">' + (r[1] ? (r[1].length === 10 ? dlong(r[1]) : r[1]) : '<span class="small">Needs more dates</span>') + '</td></tr>'; }).join('');
      if (e) res.focus();
    }
    cf.addEventListener('submit', run);
    doc.getElementById('ck-sample').addEventListener('click', function () {
      [['ck-cheque', '2026-09-20'], ['ck-presented', '2026-10-01'], ['ck-memo', '2026-10-05'], ['ck-sent', '2026-10-30'], ['ck-delivered', '2026-11-03']].forEach(function (p) { doc.getElementById(p[0]).value = p[1]; });
      run({ preventDefault: function () {} });
    });
  }

  /* ---------- Early access form: prepares a GitHub issue, sends nothing ---------- */
  var form = doc.getElementById('contact-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var ok = true;
      form.querySelectorAll('[data-required]').forEach(function (f) {
        var err = doc.getElementById(f.id + '-err'), bad = !f.value.trim();
        err.textContent = bad ? 'This field is required.' : '';
        f.setAttribute('aria-invalid', String(bad)); if (bad && ok) f.focus(); if (bad) ok = false;
      });
      if (!ok) return;
      var title = 'Early access: ' + doc.getElementById('c-product').value + ' (' + doc.getElementById('c-role').value + ')';
      var body = 'Name: ' + doc.getElementById('c-name').value.trim() + '\nOrganisation: ' + (doc.getElementById('c-org').value.trim() || '-') + '\n\n' + doc.getElementById('c-msg').value.trim();
      doc.getElementById('form-link').href = form.getAttribute('data-issues') + '?title=' + encodeURIComponent(title) + '&body=' + encodeURIComponent(body);
      form.hidden = true; var done = doc.getElementById('form-ok'); done.hidden = false; done.focus();
    });
  }

  /* ---------- Sign in and sign up: real accounts on the Tarikh server ---------- */
  var af = doc.getElementById('auth-form');
  if (af) {
    var kind = af.getAttribute('data-kind'), msg = doc.getElementById('a-msg');
    var next = new URLSearchParams(location.search).get('next') || 'app/index.html';
    if (!/^[a-z0-9_\-\/\.]+(#[A-Za-z0-9_\-]+)?$/i.test(next) || next.indexOf('//') >= 0) next = 'app/index.html';
    af.addEventListener('submit', function (e) {
      e.preventDefault();
      var body = { email: doc.getElementById('a-email').value, password: doc.getElementById('a-pass').value };
      if (kind === 'signup') { body.name = doc.getElementById('a-name').value; body.chambers = doc.getElementById('a-chambers').value; var k = af.querySelector('input[name=kind]:checked'); body.kind = k ? k.value : 'advocate'; }
      var btn = af.querySelector('button[type=submit]'); btn.disabled = true; msg.textContent = '';
      fetch('api/auth/' + kind, { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'same-origin', body: JSON.stringify(body) })
        .then(function (r) { return r.json().catch(function () { return { error: 'The Tarikh server did not answer.' }; }).then(function (j) { return { ok: r.ok, j: j, status: r.status }; }); })
        .then(function (res) {
          btn.disabled = false;
          if (res.ok) { location.href = next; return; }
          msg.textContent = res.status === 404 || res.status === 405 ? 'This copy of the site has no Tarikh server behind it, so accounts cannot be created here. Run Tarikh on your computer (see the README) and open it there.' : (res.j.error || 'Something went wrong. Try again.');
        }, function () { btn.disabled = false; msg.textContent = 'This copy of the site has no Tarikh server behind it, so accounts cannot be created here. Run Tarikh on your computer (see the README) and open it there.'; });
    });
  }

  window.Tarikh = { mountLongTable: mountLongTable, leafHTML: leafHTML, statusOf: statusOf, windowsOf: windowsOf, chip: chip, monthHTML: monthHTML, eventsFor: eventsFor, esc: esc, plural: plural, dshort: dshort, dlong: dlong, MON: MON, MONTH: MONTH, WD: WD, dow: dow, STAGE_LABEL: STAGE_LABEL };
})();
