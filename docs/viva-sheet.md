# Viva sheet: Tarikh and AI-901

Read this twice. Answers are short on purpose: say the first sentence, then stop and let the examiner ask the next thing.

## 1. The 60-second pitch

Tarikh is a litigation platform for cheque-bounce cases under Section 138 of the Negotiable Instruments Act. Advocates and lenders create an account and keep their matters on the server. It reads the cheque, the bank's return memo and the demand notice with a gpt-4.1-mini model I fine-tuned on labelled sample papers, asks the advocate for the dates that are on no paper, counts the four statutory periods in ordinary Python, keeps hearings, drafts, settlements and an audit log, and drafts a brief in which every sentence cites a fact. A named advocate approves it before it can be read aloud. A voice note is transcribed with Azure Speech and masked with Azure AI Language before any model sees it.

**Demo order (3 minutes):** create an account, load the sample matters, read Today ("what runs out first"), open Sharma Steel Traders v. Kalra Fabricators, show the calendar leaf with the last day to file, drag a date on the clocks and say "nothing is saved", record a hearing, open Settlement, open Activity to show the audit log, then Portfolio: import the sample return file and allocate three matters. Finish on Check, the free public tool.

## 2. AI-901 concepts, each tied to something you built

**What are the two domains of AI-901?** Identify AI concepts and capabilities (40-45%), and implement AI solutions by using Microsoft Foundry (55-60%). Skills measured as of 15 April 2026.

**Name the six responsible AI principles and one place each shows up in Tarikh.**
- Fairness: nothing scores or ranks a person; every matter gets the same arithmetic.
- Reliability and safety: dates come from tested code; missing dates are named, never guessed; low confidence is flagged in words.
- Privacy and security: transcripts masked before reasoning; Entra ID sign-in, no keys in files.
- Inclusiveness: English, Hindi, Punjabi voice where offered; keyboard use; text table for the clock; no colour-only status.
- Transparency: source chips, Show on paper, visible tool calls, replay banner.
- Accountability: a named advocate approves; audit trail.

**How does a generative model work, in two sentences?** It turns text into tokens and predicts the next token given everything before it, one at a time. It does not calculate or look things up, which is why Tarikh counts dates in code.

**What are tokens, a context window, temperature?** A token is a piece of a word. The context window is how many tokens the model can consider at once. Temperature controls how random the choice of next token is; low is steadier.

**System prompt versus user prompt?** The system prompt sets the rules and role (Tarikh's agent prompt forbids calculating dates). The user prompt is the question.

**How did you choose the model?** By capability first, then by what my subscription allowed. I needed a model that reads images and returns structured output. In Korea Central my Azure for Students subscription had 0 tokens per minute for every base chat model, and the portal refused gpt-4.1 for insufficient quota. It did have 500,000 tokens per minute for fine-tuned gpt-4.1-mini on the Developer tier. So I fine-tuned gpt-4.1-mini on 30 labelled sample papers, kept 9 aside for validation, and deployed it as `tarikh-reader`.

**What is fine-tuning, and why did it help here?** Supervised fine-tuning trains a base model further on examples of input and the exact answer wanted. Each of my examples is one paper image, the same instruction the desk sends, and the JSON answer. It teaches the layout of Indian cheques, memos and notices and the answer format. The Developer tier charges per token with no hourly hosting fee, and a deployment lasts 24 hours, so I renew it on the days I use the desk.

**How do you know the reader is right?** I don't trust it blindly. `tools.evaluate_reader` checks all 39 fields on the 9 validation papers it never trained on. And in the desk every value read by the model is marked until an advocate confirms it, and the dates no paper shows are always asked for.

**Deployment options and configuration?** A model must be deployed to a Foundry resource before it can be called; the deployment has a name, a model and a deployment type (Standard, Global Standard, Provisioned, and Developer for fine-tuned models), and availability and quota depend on the region. Mine is `tarikh-reader`, Developer tier, in the project `tarikh` of the resource `tarikh-24bai70769`, resource group `tarikh-rg`, Korea Central.

**Which AI workloads does Tarikh use?** Information extraction (the fine-tuned reader; Content Understanding where the region has it), text analysis (PII), speech recognition and synthesis (Azure Speech), generative AI (brief), agentic AI (the two-tool agent), and a little computer vision (cheque image observations).

**Text analysis techniques?** Keyword extraction, entity detection, sentiment analysis, summarisation, and PII detection. I used PII redaction.

**Speech recognition versus synthesis?** Recognition turns audio into text (fast transcription for a recorded file); synthesis turns text into audio (neural voice for reading the approved brief).

**What is Content Understanding?** An Azure service that turns documents, images, audio and video into structured fields using analyzers. A custom analyzer extends a base analyzer with your own field schema. Each field comes back with a confidence and a location on the page.

**What is an agent?** A model plus instructions plus tools. Mine has two function tools, `get_deadlines` and `get_fact`, both read-only and bound to one matter. With function calling the agent asks for a call, my application runs it and sends the result back.

**Computer vision and image generation?** Vision interprets images (I ask the model what is visible on a cheque). Image generation creates new images; I did not use it, because nothing in the case desk needs it.

**Foundry portal or SDK?** The portal is for trying a deployed model and testing an agent; the SDK is how an application calls them. Function definitions for an agent are added with the SDK or REST, not in the portal.

## 3. Design questions about Tarikh

**Why are deadlines not computed by the model?** Models predict text; they do not calculate. A one-day error can end a case. The engine is about a hundred lines of Python with boundary tests for month-end, leap year and missing dates.

**What does "earlier, safer date" mean?** The Act says "one month". Two usual ways of ending a month differ by a day (the day before the same date, or the same date). The engine shows the earlier. Court holidays and condonation of delay are left to the advocate.

**What is a limitation of that?** Courts also differ on whether the day of receipt counts. The engine does not count it, as in the Allahabad judgment I cite. A court that did would end each period a day sooner, so the screen asks the advocate to confirm every date.

**Why "Running" and "Ended" for the drawer's 15 days, and never "Missed"?** That clock belongs to the other side. Missing it is the drawer's failure, not the payee's.

**What is the source rule?** Every claim in the brief must cite at least one fact identifier that exists. Otherwise it is dropped and listed. That is `validate_brief`.

**Why mask before reasoning, and what can still go wrong?** A client's phone number does not need to reach a model. Masking covers the transcript. The extracted facts, including party names, do reach the model when a brief is drafted. PII detection can also miss a value, so the original and masked text are shown side by side.

**Why one conversation per question for the agent?** So that nothing from an earlier answer leaks into the next, and so that the tools only ever see the one matter.

**Why Korea Central?** The Azure for Students policy allowed only five regions: Central India, East Asia, Indonesia Central, Korea Central and UAE North. South India and every other region were refused. Of the five, only Korea Central and UAE North have the Foundry Agent Service, and Speech lists Korea Central. None has Content Understanding, which is why the reader is a model with a strict JSON schema; the Content Understanding reader stays in the code behind one setting.

**Why Entra ID and no keys?** `az login` and `DefaultAzureCredential` mean no secret sits in a file or a repository. The roles needed are Cognitive Services User and Foundry User.

**What is record and replay for?** Every Azure call passes through a recorder. In replay mode it serves recorded responses and the page shows a banner, so the project can be shown without a connection without pretending that the answers are live.

**Why no front-end framework?** The interface is a few hundred lines of plain HTML, CSS and JavaScript. No build step means nothing extra to break on the day.

**Why does the interface look like a calendar?** A cheque case is a sequence of dates, so the recurring object is the Indian tear-off wall calendar: a red month band, a black numeral and the Hindi weekday. Black, white and calendar red; amber means a person must act, green means settled or approved. Every status is also written in words.

**How are accounts kept safe?** Passwords are hashed with scrypt and a random salt and never stored; the session is a random 32-byte token in an HttpOnly cookie for 14 days. Every matter has an owner, and someone else's matter answers as if it does not exist.

**How many tests?** 145 automated checks: 108 server checks, 26 browser checks (9 of the case desk, 17 of the website and platform) and 11 checks of the deadline engine in the browser.

## 4. Questions about the report

**Which chapters are there?** 1 Introduction, 2 Weekly Report, 3 Requirements and Design, 4 Implementation, 5 Testing, Results and Responsible AI, 6 Conclusions and Recommendations, then appendices and references.

**How many tests?** 88 automated checks outside the browser and 9 browser checks at the last run, and the accessibility scan reported no violations. The deadline boundary cases in Table 5.2 are executed when the report is built.

**What did you not do?** I did not train a model. All services are pre-built Azure services. I did not build court-holiday handling, filing, or several users.

**What would you do next?** A holiday calendar, showing both ways of counting the day of receipt, roles for a junior and a senior, and a measurement of reading accuracy on more real papers.

## 5. Hard questions, honest answers

- **"Is this legal advice?"** No. It counts dates and drafts a note for an advocate, who approves it. Every date is labelled for the advocate to confirm.
- **"Can the model make up a fact in the brief?"** It can try, but a claim with no valid source is dropped. A claim that cites a real fact but misreads it is possible, which is why the advocate approves.
- **"How accurate is the reading of the cheque?"** Use the numbers from your evidence run (Table 5.3). Say how many fields were read correctly and how many you corrected by hand, and that three samples show the pipeline works but do not prove accuracy.
- **"What if Azure is down?"** The deadline engine, the store and the interface still work. Replay mode serves recorded responses and says so.
- **"Why not use one big agent for everything?"** Then the legal arithmetic would be in a model. Putting the steps in code keeps each one testable.

## 6. One-line glossary

Analyzer: a Content Understanding definition of what to extract. Cassette: a recorded request and response. Entra ID: the Azure sign-in service. Fact: one value read from a paper, with confidence and location. Function calling: the agent asks, the app runs the function. PII: personal data such as a phone number. Responses API: how the app calls the deployed model. Source chip: the label under a brief sentence that names the fact it came from.
