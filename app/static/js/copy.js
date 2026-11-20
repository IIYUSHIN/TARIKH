// Every string the interface speaks, in one place so tone stays consistent. Law-office plain; no decoration.
export const DOC_LABEL = { cheque: "Cheque", return_memo: "Bank return memo", demand_notice: "Demand notice" };
export const ADD_LABEL = { cheque: "Add the cheque", return_memo: "Add the return memo", demand_notice: "Add the demand notice" };
export const READING = {
  cheque: "Reading the cheque and checking it for signature and stamps",
  return_memo: "Reading the bank's return memo",
  demand_notice: "Reading the demand notice",
};
export const DATE_KEYS = new Set(["cheque_date", "presented_on", "return_date", "memo_received_on", "notice_date",
  "notice_sent_on", "notice_delivered_on"]);
export const NEEDS = {
  validity: "the cheque date",
  notice: "the date you received the bank's return memo",
  payment: "the date the drawer received the notice",
  complaint: "the date the drawer received the notice",
};
export const STATUS_WORD = { unknown: "Cannot be worked out", upcoming: "Not yet open", open: "Open", closing: "Closing soon",
  expired: "Missed", met: "Met" };
export const MODE = {
  replay: (when) => `Replay of a recorded run${when ? ", " + when : ""}. No live Azure calls are being made.`,
  live: (dep) => `Live. Model deployment ${dep}.`,
};
export const SAFEGUARDS = [
  ["Fairness", "Nothing ranks or scores a person. The model only drafts a brief from papers, and every sentence in it must cite a fact."],
  ["Reliability and safety", "A date the paper does not show is never guessed. A value read with low confidence is flagged. Deadlines come from a rule engine with written tests, not from the model."],
  ["Privacy and security", "A client's spoken account has names, numbers and addresses masked by Azure AI Language before any model sees it. Sign-in is by your Azure identity; no keys are stored."],
  ["Inclusiveness", "The client can speak in English, Hindi or Punjabi where Azure Speech supports it, and the approved brief can be read back aloud. Every control works by keyboard."],
  ["Transparency", "Each fact links to the place on the paper it was read from. Model-written text says which deployment wrote it and that it is a draft."],
  ["Accountability", "A named advocate approves the brief before it can be read to a client. Every edit and approval is written to the matter's audit trail."],
];
export const TXT = {
  mattersTitle: "Matters",
  mattersEmpty: "No matters yet. Start one for a client, or open the fictional sample to see how the desk works.",
  newMatter: "New matter", newMatterLabel: "Matter title", createMatter: "Create matter",
  openSample: "Open the fictional sample matter",
  sampleNote: "Fictional sample. The return memo reached the advocate on 5 Oct 2026, the notice went out on 30 Oct and the drawer received it on 3 Nov. Enter those three dates in the ledger.",
  papers: "The papers", ledger: "The ledger", brief: "The brief", ask: "Ask the desk", voice: "The client’s account",
  safeguards: "Safeguards", clock: "The clock",
  showOnPaper: "Show on paper", markChecked: "Mark as checked", checked: "Checked",
  notOnPaper: "Not on the paper. Enter it from your file.",
  noFacts: "Nothing read yet. Add the cheque first.",
  draftBrief: "Draft the brief", redraft: "Redraft the brief",
  redraftWarn: "Redrafting clears the approval. You will need to approve again.",
  needCheque: "Add the cheque first. The brief needs at least one fact read from it.",
  approve: "Approve brief", reviewer: "Reviewing advocate",
  needBrief: "Draft the brief before approving it.", needName: "Enter the reviewing advocate’s name to approve.",
  readAloud: "Read to the client", askButton: "Ask", askLabel: "Question about this matter",
  askHint: "For example: When must the complaint be filed?",
  record: "Record", stop: "Stop recording", uploadAudio: "Upload a recording",
  confirmLaw: "Court holidays and delay condonation are for the advocate to confirm.",
  copyReplay: "Recorded", draftedBy: (m) => `Drafted by ${m}. Not legal advice.`,
};
