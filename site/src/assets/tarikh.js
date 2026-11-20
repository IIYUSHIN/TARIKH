/* Tarikh site behaviour. No dependencies. Everything works without it except the live table. */
(function () {
  'use strict';
  var E = window.TarikhEngine;
  var doc = document;
  doc.documentElement.classList.add('js');

  /* ---------- Menu ---------- */
  var btn = doc.querySelector('.menu-btn');
  var nav = doc.getElementById('site-nav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.textContent = open ? 'Close' : 'Menu';
    });
    doc.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('open')) { btn.click(); btn.focus(); }
    });
  }

  /* ---------- Settle: reveal once when scrolled into view ---------- */
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var revealTargets = doc.querySelectorAll('.rise, .stamp-in, .ruler, .dropped');
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealTargets.forEach(function (el) { io.observe(el); });
  } else {
    revealTargets.forEach(function (el) { el.classList.add('in'); });
  }

  /* ---------- Scroll story: the step in the middle of the screen owns the stage ---------- */
  var steps = doc.querySelectorAll('.story-steps li');
  var panes = doc.querySelectorAll('.story-stage .pane');
  if (steps.length && panes.length && 'IntersectionObserver' in window) {
    var so = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var n = en.target.getAttribute('data-step');
        steps.forEach(function (s) { s.classList.toggle('on', s === en.target); });
        panes.forEach(function (p) { p.classList.toggle('on', p.getAttribute('data-pane') === n); });
      });
    }, { rootMargin: '-45% 0px -45% 0px', threshold: 0 });
    steps.forEach(function (s) { so.observe(s); });
    steps[0].classList.add('on');
    panes[0].classList.add('on');
  } else {
    steps.forEach(function (s) { s.classList.add('on'); });
  }

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
    var heading = root.getAttribute('data-heading') || 'The long table';
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
      '<text class="s-num" x="86" y="114" text-anchor="middle" font-family="Bodoni Moda, serif" font-size="62" font-weight="500" fill="currentColor" letter-spacing="-2"></text>' +
      '<text class="s-word" x="86" y="138" text-anchor="middle" font-family="Instrument Sans, sans-serif" font-size="11" font-weight="700" letter-spacing="2.4" fill="currentColor"></text>' +
      '<path d="M42 58h88" stroke="currentColor" stroke-width="1"/>' +
      '<text x="86" y="48" text-anchor="middle" font-family="Instrument Sans, sans-serif" font-size="9" font-weight="700" letter-spacing="2.2" fill="currentColor">SAMPLE MATTER</text>' +
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

  /* ---------- Docket: statuses are computed by the engine, never typed ---------- */
  doc.querySelectorAll('[data-docket] li[data-cheque]').forEach(function (li) {
    var today = li.closest('[data-docket]').getAttribute('data-today');
    var w = E.computeWindows({ cheque: li.getAttribute('data-cheque'), presented: li.getAttribute('data-presented'), memo: li.getAttribute('data-memo'), sent: li.getAttribute('data-sent'), delivered: li.getAttribute('data-delivered'), today: today });
    var c = w.complaint, st = li.querySelector('.st'), line = li.querySelector('.when');
    var cls, txt;
    if (c.status === 'expired') { cls = 'gone'; txt = 'Window closed ' + plural(E.daysBetween(c.closes, today), 'day', 'days') + ' ago'; }
    else if (c.status === 'upcoming') { cls = 'calm'; txt = 'Opens in ' + plural(E.daysBetween(today, c.opens), 'day', 'days'); }
    else { cls = c.daysLeft <= 7 ? 'hot' : (c.daysLeft <= 21 ? 'warn' : 'calm'); txt = plural(c.daysLeft, 'day', 'days') + ' left'; }
    st.className = 'st ' + cls; st.textContent = txt;
    line.textContent = 'Complaint ' + E.short(c.opens) + ' to ' + E.short(c.closes);
    // Urgency order: open windows by days left, then ones not yet open by when they open, then closed ones, newest first.
    var rank = c.status === 'expired' ? 3e6 - E.daysBetween(c.closes, today) : (c.status === 'upcoming' ? 1e6 + E.daysBetween(today, c.opens) : c.daysLeft);
    li.setAttribute('data-rank', String(rank));
  });
  doc.querySelectorAll('[data-docket]').forEach(function (ul) {
    Array.prototype.slice.call(ul.children).sort(function (a, b) { return (+a.getAttribute('data-rank')) - (+b.getAttribute('data-rank')); }).forEach(function (li) { ul.appendChild(li); });
  });

  /* ---------- Approval gate (demo: nothing is saved or sent) ---------- */
  var ap = doc.getElementById('approve-form');
  if (ap) {
    ap.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = doc.getElementById('approver'), err = doc.getElementById('approver-err'), box = doc.getElementById('approve-check');
      var bad = !name.value.trim() || !box.checked;
      err.textContent = !name.value.trim() ? 'Type your name to approve.' : (!box.checked ? 'Tick the box to confirm you checked each footnote.' : '');
      if (bad) { (!name.value.trim() ? name : box).focus(); return; }
      var out = doc.getElementById('approve-ok');
      out.textContent = 'Approved by ' + name.value.trim() + ' on ' + E.long(ap.getAttribute('data-today')) + '. In the live desk this is written to the audit log. Here, nothing is saved or sent.';
      ap.hidden = true; out.hidden = false; out.focus();
    });
  }

  /* ---------- Contact: builds a GitHub issue draft. Nothing is sent until the person presses Submit on GitHub ---------- */
  var form = doc.getElementById('contact-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var ok = true;
      form.querySelectorAll('[data-required]').forEach(function (f) {
        var err = doc.getElementById(f.id + '-err');
        var bad = !f.value.trim();
        err.textContent = bad ? 'This field is required.' : '';
        f.setAttribute('aria-invalid', bad ? 'true' : 'false');
        if (bad && ok) { f.focus(); }
        if (bad) ok = false;
      });
      if (!ok) return;
      var topic = doc.getElementById('c-topic').value;
      var title = 'Contact: ' + topic;
      var body = 'From: ' + doc.getElementById('c-name').value.trim() + '\n\n' + doc.getElementById('c-msg').value.trim();
      var url = form.getAttribute('data-issues') + '?title=' + encodeURIComponent(title) + '&body=' + encodeURIComponent(body);
      var link = doc.getElementById('form-link'); link.href = url;
      form.hidden = true;
      var done = doc.getElementById('form-ok'); done.hidden = false; done.focus();
    });
  }
})();
