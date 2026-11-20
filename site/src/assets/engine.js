/* Tarikh date engine. Plain arithmetic, no model, no network, no dependencies.
 * Mirrors app/deadlines.py after decision 0004; the two are kept honest by tests on both sides.
 * Dates are ISO strings (YYYY-MM-DD) and are handled in UTC so a time zone can never move a day. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.TarikhEngine = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var DAY = 86400000;
  var CLOSING_DAYS = 5;
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var MONTH = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  var WEEKDAY = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  function parse(iso) {
    var p = iso.split('-');
    return Date.UTC(+p[0], +p[1] - 1, +p[2]);
  }
  function iso(ms) {
    var d = new Date(ms);
    return d.getUTCFullYear() + '-' + String(d.getUTCMonth() + 1).padStart(2, '0') + '-' + String(d.getUTCDate()).padStart(2, '0');
  }
  function addDays(date, n) { return iso(parse(date) + n * DAY); }
  function daysBetween(a, b) { return Math.round((parse(b) - parse(a)) / DAY); }
  function weekday(date) { return WEEKDAY[new Date(parse(date)).getUTCDay()]; }
  function short(date) { var d = new Date(parse(date)); return d.getUTCDate() + ' ' + MON[d.getUTCMonth()]; }
  function long(date) { var d = new Date(parse(date)); return d.getUTCDate() + ' ' + MONTH[d.getUTCMonth()] + ' ' + d.getUTCFullYear(); }

  function lastOfMonth(year, month0) { return new Date(Date.UTC(year, month0 + 1, 0)).getUTCDate(); }

  /* The same calendar date `months` later; the last day of the month when that date does not exist. */
  function monthAfter(date, months) {
    var d = new Date(parse(date));
    var idx = d.getUTCFullYear() * 12 + d.getUTCMonth() + months;
    var y = Math.floor(idx / 12), m = idx % 12;
    return iso(Date.UTC(y, m, Math.min(d.getUTCDate(), lastOfMonth(y, m))));
  }

  /* Last day of a period of `months` months that begins on `date` (day one = date): the day before
   * the same calendar date, or the last day of the shorter month when that date does not exist. */
  function monthPeriodEnd(date, months) {
    var d = new Date(parse(date));
    var idx = d.getUTCFullYear() * 12 + d.getUTCMonth() + months;
    var y = Math.floor(idx / 12), m = idx % 12;
    var last = lastOfMonth(y, m);
    if (d.getUTCDate() > last) return iso(Date.UTC(y, m, last));
    return iso(Date.UTC(y, m, d.getUTCDate()) - DAY);
  }

  function status(opens, closes, today) {
    if (!opens || !closes || !today) return { status: 'unknown', daysLeft: null };
    if (daysBetween(today, opens) > 0) return { status: 'upcoming', daysLeft: null };
    if (daysBetween(today, closes) < 0) return { status: 'expired', daysLeft: null };
    var left = daysBetween(today, closes);
    return { status: left <= CLOSING_DAYS ? 'closing' : 'open', daysLeft: left };
  }

  /* inputs: cheque, presented, memo, sent, delivered, today (all optional ISO strings). */
  function computeWindows(i) {
    i = i || {};
    var today = i.today || null;

    // 1. Cheque presented within its three months (proviso (a)).
    var vCloses = i.cheque ? monthPeriodEnd(i.cheque, 3) : null;
    var vStatus = 'unknown';
    if (i.cheque && i.presented) vStatus = parse(i.presented) <= parse(vCloses) ? 'met' : 'expired';
    var validity = { opens: i.cheque || null, closes: vCloses, status: vStatus, daysLeft: null };

    // 2. Demand notice within 30 days of receiving the bank's memo (proviso (b)).
    var nOpens = i.memo || null;
    var nCloses = i.memo ? addDays(i.memo, 30) : null;
    var notice;
    if (i.sent && nCloses) {
      notice = { opens: nOpens, closes: nCloses, status: parse(i.sent) <= parse(nCloses) ? 'met' : 'expired', daysLeft: null };
    } else {
      var ns = status(nOpens, nCloses, today);
      notice = { opens: nOpens, closes: nCloses, status: ns.status, daysLeft: ns.daysLeft };
    }

    // 3. The drawer's fifteen days, from the day after the notice reached them (proviso (c)).
    var pOpens = i.delivered ? addDays(i.delivered, 1) : null;
    var pCloses = i.delivered ? addDays(i.delivered, 15) : null;
    var ps = status(pOpens, pCloses, today);
    var payment = { opens: pOpens, closes: pCloses, status: ps.status, daysLeft: ps.daysLeft };

    // 4. The complaint, within one month of the cause of action (s.142(1)(b)). The cause-of-action day
    // is excluded (Econ Antri v. Rom Industries), so the last day has the same date one month on.
    var cOpens = pCloses ? addDays(pCloses, 1) : null;
    var cCloses = cOpens ? monthAfter(cOpens, 1) : null;
    var cSafe = cOpens ? monthPeriodEnd(cOpens, 1) : null;
    var cs = status(cOpens, cCloses, today);
    var complaint = { opens: cOpens, closes: cCloses, conservativeCloses: cSafe, status: cs.status, daysLeft: cs.daysLeft };

    return { validity: validity, notice: notice, payment: payment, complaint: complaint };
  }

  return {
    computeWindows: computeWindows, monthAfter: monthAfter, monthPeriodEnd: monthPeriodEnd,
    addDays: addDays, daysBetween: daysBetween, weekday: weekday, short: short, long: long,
    MON: MON, MONTH: MONTH, WEEKDAY: WEEKDAY
  };
});
