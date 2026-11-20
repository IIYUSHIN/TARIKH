// The site's date engine must give the same answers as app/deadlines.py (decision 0004).
const test = require('node:test');
const assert = require('node:assert/strict');
const E = require('../src/assets/engine.js');

test('monthAfter keeps the calendar date and clamps to the shorter month', () => {
  assert.equal(E.monthAfter('2026-11-19', 1), '2026-12-19');
  assert.equal(E.monthAfter('2026-12-19', 1), '2027-01-19');
  assert.equal(E.monthAfter('2026-01-31', 1), '2026-02-28');
  assert.equal(E.monthAfter('2024-01-31', 1), '2024-02-29');
});

test('monthPeriodEnd ends the day before the same date, clamped when the date does not exist', () => {
  assert.equal(E.monthPeriodEnd('2026-04-08', 1), '2026-05-07');
  assert.equal(E.monthPeriodEnd('2026-01-10', 3), '2026-04-09');
  assert.equal(E.monthPeriodEnd('2026-01-31', 1), '2026-02-28');
  assert.equal(E.monthPeriodEnd('2026-11-30', 3), '2027-02-28');
});

test('the site demo matter: complaint 19 Nov to 19 Dec, conservative 18 Dec, 29 days left', () => {
  const w = E.computeWindows({ cheque: '2026-09-20', presented: '2026-10-01', memo: '2026-10-05', sent: '2026-10-30', delivered: '2026-11-03', today: '2026-11-20' });
  assert.deepEqual([w.validity.closes, w.validity.status], ['2026-12-19', 'met']);
  assert.deepEqual([w.notice.opens, w.notice.closes, w.notice.status], ['2026-10-05', '2026-11-04', 'met']);
  assert.deepEqual([w.payment.opens, w.payment.closes, w.payment.status], ['2026-11-04', '2026-11-18', 'expired']);
  assert.deepEqual([w.complaint.opens, w.complaint.closes, w.complaint.conservativeCloses], ['2026-11-19', '2026-12-19', '2026-12-18']);
  assert.deepEqual([w.complaint.status, w.complaint.daysLeft], ['open', 29]);
});

test('published example: notice delivered 5 May 2017, drawer 6 to 20 May', () => {
  const w = E.computeWindows({ delivered: '2017-05-05', today: '2017-05-10' });
  assert.deepEqual([w.payment.opens, w.payment.closes], ['2017-05-06', '2017-05-20']);
});

test('published example: delivered 23 March 2026, complaint 8 April to 8 May', () => {
  const w = E.computeWindows({ delivered: '2026-03-23', today: '2026-04-10' });
  assert.equal(w.payment.closes, '2026-04-07');
  assert.deepEqual([w.complaint.opens, w.complaint.closes, w.complaint.conservativeCloses], ['2026-04-08', '2026-05-08', '2026-05-07']);
});

test('nothing is guessed when a date is missing', () => {
  const w = E.computeWindows({ today: '2026-05-01' });
  for (const k of ['validity', 'notice', 'payment', 'complaint']) assert.equal(w[k].status, 'unknown');
  assert.equal(w.complaint.closes, null);
  const sentOnly = E.computeWindows({ sent: '2026-03-10', memo: '2026-03-01', today: '2026-03-12' });
  assert.equal(sentOnly.payment.status, 'unknown');
  assert.equal(sentOnly.complaint.closes, null);
});

test('notice: thirty days from the memo, met on the last day, expired a day later', () => {
  const base = { memo: '2026-03-01', today: '2026-04-20' };
  assert.equal(E.computeWindows({ ...base, sent: '2026-03-31' }).notice.status, 'met');
  assert.equal(E.computeWindows({ ...base, sent: '2026-04-01' }).notice.status, 'expired');
});

test('status: closing within five days, open otherwise; upcoming before; expired after', () => {
  const at = (today) => E.computeWindows({ delivered: '2026-06-01', today }).payment;
  assert.deepEqual([at('2026-06-11').status, at('2026-06-11').daysLeft], ['closing', 5]);
  assert.deepEqual([at('2026-06-10').status, at('2026-06-10').daysLeft], ['open', 6]);
  const c = (today) => E.computeWindows({ delivered: '2026-06-01', today }).complaint;
  assert.equal(c('2026-06-05').status, 'upcoming');
  assert.equal(c('2026-08-01').status, 'expired');
});

test('validity: presented on the last day is met, a day later is expired', () => {
  const v = (presented) => E.computeWindows({ cheque: '2026-01-10', presented, today: '2026-05-01' }).validity;
  assert.equal(v('2026-04-09').status, 'met');
  assert.equal(v('2026-04-10').status, 'expired');
});

test('weekday names and the display format', () => {
  assert.equal(E.weekday('2026-12-19'), 'Saturday');
  assert.equal(E.weekday('2026-11-20'), 'Friday');
  assert.equal(E.short('2026-12-19'), '19 Dec');
  assert.equal(E.long('2026-12-19'), '19 December 2026');
});

test('daysBetween and addDays work across month and year ends', () => {
  assert.equal(E.daysBetween('2026-11-20', '2026-12-19'), 29);
  assert.equal(E.addDays('2026-12-30', 3), '2027-01-02');
});
