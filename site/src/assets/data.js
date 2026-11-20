/* Tarikh sample data. Every party, advocate, lender and case number here is fictional.
   Statuses are never stored: they are computed from dates by TarikhEngine at render time. */
(function (root) {
  'use strict';
  var TODAY = '2026-11-20';

  var STAGES = [
    { k: 'notice', label: 'Send notice' },
    { k: 'payment', label: 'Drawer’s 15 days' },
    { k: 'file', label: 'File complaint' },
    { k: 'cognizance', label: 'Cognizance' },
    { k: 'summons', label: 'Summons' },
    { k: 'evidence', label: 'Evidence' },
    { k: 'arguments', label: 'Arguments' },
    { k: 'settled', label: 'Settled' },
    { k: 'decided', label: 'Decided' }
  ];

  /* ---------- The chambers: a fictional advocate's desk ---------- */
  var CHAMBERS = { name: 'Grewal & Associates', advocate: 'Adv. S. Grewal', city: 'Chandigarh' };

  function m(o) { return o; }
  var MATTERS = [
    m({ id: 'KF-1042', complainant: 'Sharma Steel Traders', accused: 'Kalra Fabricators', amount: 485000, chequeNo: '004718', bank: 'Northern Sample Bank, Sector 22, Chandigarh',
        cheque: '2026-09-20', presented: '2026-10-01', returned: '2026-10-03', reason: 'Funds insufficient', memo: '2026-10-05', sent: '2026-10-30', delivered: '2026-11-03',
        stage: 'file', court: 'Judicial Magistrate First Class, Chandigarh', papers: true, phone: '+91 98•• ••4127', email: 'accounts@kalra-fab.example',
        drafts: [{ t: 'Complaint with synopsis', s: 'Awaiting approval' }, { t: 'Affidavit of service details', s: 'Draft' }] }),
    m({ id: 'DC-0987', complainant: 'Bajwa Agro Inputs', accused: 'Dhillon Cold Storage', amount: 640000, chequeNo: '118204', bank: 'Sample Co-operative Bank, Ludhiana',
        cheque: '2026-09-01', presented: '2026-09-10', returned: '2026-09-11', reason: 'Payment stopped by drawer', memo: '2026-09-13', sent: '2026-10-05', delivered: '2026-10-09',
        stage: 'file', court: 'Judicial Magistrate First Class, Ludhiana', drafts: [{ t: 'Complaint with synopsis', s: 'Draft' }] }),
    m({ id: 'MA-1103', complainant: 'Gill Tractors', accused: 'Mehra Agro Supplies', amount: 275000, chequeNo: '330917', bank: 'Northern Sample Bank, Patiala',
        cheque: '2026-10-05', presented: '2026-10-15', returned: '2026-10-16', reason: 'Funds insufficient', memo: '2026-10-18', sent: '2026-11-12', delivered: '2026-11-14',
        stage: 'payment', court: 'Judicial Magistrate First Class, Patiala', drafts: [] }),
    m({ id: 'RM-1121', complainant: 'Sethi Pharma Distributors', accused: 'Rana Medicos', amount: 192500, chequeNo: '076441', bank: 'Sample Urban Bank, Mohali',
        cheque: '2026-10-20', presented: '2026-10-28', returned: '2026-10-29', reason: 'Account closed', memo: '2026-11-02', sent: null, delivered: null,
        stage: 'notice', court: 'Judicial Magistrate First Class, Mohali', drafts: [{ t: 'Demand notice', s: 'Awaiting approval' }] }),
    m({ id: 'PB-1130', complainant: 'Arora Packaging', accused: 'Preet Bakers', amount: 68000, chequeNo: '501288', bank: 'Northern Sample Bank, Kharar',
        cheque: '2026-11-01', presented: '2026-11-10', returned: '2026-11-12', reason: 'Signature differs', memo: null, sent: null, delivered: null,
        stage: 'notice', court: 'Judicial Magistrate First Class, Kharar', missing: ['Date the return memo reached the client'], drafts: [] }),
    m({ id: 'CH-0905', complainant: 'Chawla Hardware', accused: 'Hans Builders', amount: 340000, chequeNo: '220145', bank: 'Sample Co-operative Bank, Panchkula',
        cheque: '2026-08-10', presented: '2026-08-20', returned: '2026-08-21', reason: 'Funds insufficient', memo: '2026-08-24', sent: '2026-09-08', delivered: '2026-09-12',
        stage: 'file', court: 'Judicial Magistrate First Class, Panchkula', drafts: [{ t: 'Application for condonation of delay', s: 'Not started' }] }),
    m({ id: 'BT-0611', complainant: 'Northline Finance', accused: 'Bhatia Timber Mart', amount: 120000, chequeNo: '640032', bank: 'Sample Urban Bank, Ludhiana',
        cheque: '2025-10-02', presented: '2025-10-10', returned: '2025-10-11', reason: 'Funds insufficient', memo: '2025-10-14', sent: '2025-11-06', delivered: '2025-11-10',
        filed: '2025-12-08', caseNo: 'NACT/1452/2025', stage: 'evidence', court: 'Judicial Magistrate First Class, Ludhiana',
        hearings: [['2026-01-19', 'Cognizance taken, summons issued', 'Done'], ['2026-03-04', 'Appearance of accused', 'Adjourned: accused absent'], ['2026-04-22', 'Appearance of accused', 'Accused appeared, bail'], ['2026-06-10', 'Notice of accusation', 'Done'], ['2026-08-05', 'Complainant evidence', 'Adjourned: counsel unavailable'], ['2026-10-01', 'Complainant evidence', 'Adjourned: court on leave']],
        next: ['2026-11-24', 'Complainant evidence'], drafts: [{ t: 'Evidence affidavit, Section 145', s: 'Approved' }] }),
    m({ id: 'KS-0544', complainant: 'Kapoor Sanitary House', accused: 'K. S. Enterprises', amount: 310000, chequeNo: '009214', bank: 'Northern Sample Bank, Jalandhar',
        cheque: '2026-02-12', presented: '2026-02-20', returned: '2026-02-21', reason: 'Funds insufficient', memo: '2026-02-24', sent: '2026-03-10', delivered: '2026-03-13',
        filed: '2026-04-20', caseNo: 'NACT/0877/2026', stage: 'summons', court: 'Judicial Magistrate First Class, Jalandhar',
        hearings: [['2026-06-02', 'Pre-summoning evidence', 'Done'], ['2026-08-18', 'Service of summons', 'Not served: address locked'], ['2026-10-13', 'Service of summons', 'Served by WhatsApp, report awaited']],
        next: ['2026-11-27', 'Appearance of accused'], drafts: [{ t: 'Affidavit of service details', s: 'Approved' }] }),
    m({ id: 'JF-0410', complainant: 'Jindal Steel Stockists', accused: 'JS Fabrication Works', amount: 975000, chequeNo: '412870', bank: 'Sample Co-operative Bank, Amritsar',
        cheque: '2025-12-15', presented: '2025-12-22', returned: '2025-12-23', reason: 'Exceeds arrangement', memo: '2025-12-26', sent: '2026-01-14', delivered: '2026-01-17',
        filed: '2026-02-23', caseNo: 'NACT/0392/2026', stage: 'evidence', court: 'Judicial Magistrate First Class, Amritsar',
        hearings: [['2026-04-07', 'Cognizance taken, summons issued', 'Done'], ['2026-06-16', 'Appearance of accused', 'Accused appeared'], ['2026-09-09', 'Notice of accusation', 'Done']],
        next: ['2026-12-03', 'Application for interim compensation, Section 143A'], drafts: [{ t: 'Application under Section 143A', s: 'Awaiting approval' }] }),
    m({ id: 'MT-0322', complainant: 'Harjeet Motors', accused: 'Mann Transport Co.', amount: 225000, chequeNo: '381102', bank: 'Northern Sample Bank, Bathinda',
        cheque: '2025-09-05', presented: '2025-09-12', returned: '2025-09-13', reason: 'Funds insufficient', memo: '2025-09-16', sent: '2025-10-03', delivered: '2025-10-07',
        filed: '2025-11-17', caseNo: 'NACT/1301/2025', stage: 'evidence', court: 'Judicial Magistrate First Class, Bathinda', settlement: { total: 225000, parts: 3, paid: 1 },
        hearings: [['2026-01-12', 'Appearance of accused', 'Accused appeared'], ['2026-05-25', 'Referred to mediation', 'Terms agreed: three instalments'], ['2026-09-14', 'First instalment', 'Paid ₹75,000']],
        next: ['2026-11-26', 'Second instalment and compounding'], drafts: [{ t: 'Joint application to compound, Section 147', s: 'Draft' }] }),
    m({ id: 'VB-0219', complainant: 'Saini Electricals', accused: 'Verma Builders', amount: 1440000, chequeNo: '702556', bank: 'Sample Urban Bank, Chandigarh',
        cheque: '2025-03-03', presented: '2025-03-12', returned: '2025-03-13', reason: 'Funds insufficient', memo: '2025-03-15', sent: '2025-04-02', delivered: '2025-04-05',
        filed: '2025-05-12', caseNo: 'NACT/0618/2025', stage: 'evidence', court: 'Judicial Magistrate First Class, Chandigarh',
        hearings: [['2025-07-09', 'Appearance of accused', 'Adjourned: accused absent'], ['2025-09-17', 'Appearance of accused', 'Accused appeared'], ['2026-01-28', 'Complainant evidence', 'Done'], ['2026-05-06', 'Statement of accused, Section 313 CrPC / 351 BNSS', 'Done'], ['2026-08-26', 'Defence evidence', 'Adjourned: witness absent']],
        next: ['2026-12-08', 'Defence evidence'], drafts: [] }),
    m({ id: 'GT-0118', complainant: 'Anand Grains', accused: 'Goyal Traders', amount: 560000, chequeNo: '150903', bank: 'Northern Sample Bank, Karnal',
        cheque: '2024-12-10', presented: '2024-12-18', returned: '2024-12-19', reason: 'Funds insufficient', memo: '2024-12-21', sent: '2025-01-09', delivered: '2025-01-13',
        filed: '2025-02-24', caseNo: 'NACT/0244/2025', stage: 'arguments', court: 'Judicial Magistrate First Class, Karnal',
        hearings: [['2025-05-07', 'Appearance of accused', 'Accused appeared'], ['2025-09-30', 'Complainant evidence', 'Done'], ['2026-03-18', 'Defence evidence', 'Closed'], ['2026-09-29', 'Final arguments', 'Part heard']],
        next: ['2026-12-12', 'Final arguments'], drafts: [{ t: 'Written arguments', s: 'Draft' }] }),
    m({ id: 'PP-0730', complainant: 'Luthra Paper Mart', accused: 'Pal Printers', amount: 85000, chequeNo: '299017', bank: 'Sample Urban Bank, Mohali',
        cheque: '2026-04-01', presented: '2026-04-08', returned: '2026-04-09', reason: 'Funds insufficient', memo: '2026-04-11', sent: '2026-04-29', delivered: '2026-05-02',
        filed: '2026-06-08', caseNo: 'NACT/1103/2026', stage: 'settled', court: 'Judicial Magistrate First Class, Mohali', settlement: { total: 85000, parts: 1, paid: 1 },
        hearings: [['2026-08-20', 'Appearance of accused', 'Accused paid through the court’s online link'], ['2026-10-14', 'Compounding', 'Compounded under Section 147, no costs']],
        drafts: [] })
  ];

  /* ---------- Recover: a fictional lender's portfolio, generated deterministically ---------- */
  function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  var R = rng(138);
  function pick(a) { return a[Math.floor(R() * a.length)]; }
  var SUR = ['Bedi', 'Sandhu', 'Malhotra', 'Bains', 'Sidhu', 'Khanna', 'Brar', 'Gupta', 'Ahuja', 'Walia', 'Chopra', 'Dhaliwal', 'Kohli', 'Bhalla', 'Mittal', 'Sekhon', 'Talwar', 'Virk', 'Jain', 'Grover'];
  var BIZ = ['Kirana Store', 'Auto Parts', 'Hardware', 'Textiles', 'Dairy', 'Mobile Hub', 'Traders', 'Agencies', 'Medicos', 'Furnishers', 'Tyres', 'Electricals', 'Sweets', 'Steel', 'Enterprises'];
  var CITY = ['Ludhiana', 'Jalandhar', 'Amritsar', 'Patiala', 'Mohali', 'Chandigarh', 'Bathinda', 'Panchkula'];
  var PANEL = ['Adv. R. Bedi', 'Adv. N. Sood', 'Adv. K. Dhaliwal', 'Adv. A. Mehta'];
  var PSTAGE = ['notice', 'payment', 'file', 'cognizance', 'summons', 'summons', 'evidence', 'evidence', 'evidence', 'arguments', 'settled', 'settled', 'decided'];
  function iso(d) { return d.toISOString().slice(0, 10); }
  function add(s, n) { var d = new Date(s + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return iso(d); }

  var PORTFOLIO = [];
  for (var i = 0; i < 64; i++) {
    var st = pick(PSTAGE);
    var early = st === 'notice' || st === 'payment' || st === 'file';
    var age = early ? Math.floor(R() * 40) + 8 : Math.floor(R() * 1050) + 60;
    var cheque = add(TODAY, -age - 20);
    var presented = add(cheque, 5 + Math.floor(R() * 20));
    var memo = add(presented, 2 + Math.floor(R() * 3));
    var sent = st === 'notice' ? null : add(memo, 6 + Math.floor(R() * 20));
    var delivered = sent ? add(sent, 2 + Math.floor(R() * 4)) : null;
    var filed = early ? null : add(delivered, 18 + Math.floor(R() * 12));
    var amt = Math.round((25000 + Math.pow(R(), 2.2) * 1175000) / 500) * 500;
    var adj = early ? 0 : Math.floor(R() * (st === 'cognizance' ? 2 : 9));
    var row = {
      id: 'NF-' + String(2400 + i * 7),
      accused: pick(SUR) + ' ' + pick(BIZ), city: pick(CITY), amount: amt, stage: st,
      cheque: cheque, presented: presented, memo: memo, sent: sent, delivered: delivered, filed: filed,
      adjournments: adj, advocate: R() < 0.12 ? null : pick(PANEL),
      next: early || st === 'settled' || st === 'decided' ? null : add(TODAY, 2 + Math.floor(R() * 60)),
      recovered: st === 'settled' ? amt : (st === 'evidence' && R() < 0.2 ? Math.round(amt * 0.4 / 500) * 500 : 0)
    };
    if (st === 'payment' || st === 'file') {
      row.delivered = st === 'payment' ? add(TODAY, -Math.floor(R() * 12) - 1) : add(TODAY, -16 - Math.floor(R() * 26));
      row.sent = add(row.delivered, -3);
      row.memo = add(row.sent, -6 - Math.floor(R() * 14));
      row.presented = add(row.memo, -3);
      row.cheque = add(row.presented, -5 - Math.floor(R() * 15));
    }
    if (st === 'notice') { row.memo = add(TODAY, -2 - Math.floor(R() * 24)); row.presented = add(row.memo, -3); row.cheque = add(row.presented, -5 - Math.floor(R() * 15)); }
    PORTFOLIO.push(row);
  }

  function inr(n) {
    var s = String(Math.round(n)), last = s.slice(-3), rest = s.slice(0, -3);
    if (rest) last = ',' + last;
    return '₹' + rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + last;
  }
  function lakh(n) { return n >= 1e7 ? '₹' + (n / 1e7).toFixed(2) + ' cr' : '₹' + (n / 1e5).toFixed(1) + ' L'; }
  function find(id) { for (var j = 0; j < MATTERS.length; j++) if (MATTERS[j].id === id) return MATTERS[j]; return null; }

  root.TarikhData = { TODAY: TODAY, STAGES: STAGES, CHAMBERS: CHAMBERS, MATTERS: MATTERS, PORTFOLIO: PORTFOLIO, PANEL: PANEL, inr: inr, lakh: lakh, find: find, add: add };
})(typeof self !== 'undefined' ? self : this);
