# Viva sheet: Tarikh and AI-901

Read this twice. Answers are short on purpose: say the first sentence, then stop and let the examiner ask the next thing.

## 1. The 60-second pitch

Tarikh is a desk for one cheque-bounce case under Section 138 of the Negotiable Instruments Act. It reads the cheque, the bank's return memo and the demand notice with Azure Content Understanding, asks the advocate for the dates that are on no paper, counts the four statutory periods in ordinary Python, and drafts a short brief in which every sentence cites a fact. A named advocate approves it before it can be read aloud. A voice note is transcribed with Azure Speech and masked with Azure AI Language before any model sees it.

**Demo order (3 minutes):** open the sample matter, say "the page tells me which date is missing", type the three dates, watch the clock, drag today's marker, press Show on paper, draft the brief, point at one source chip, try Approve without a name, approve, ask the agent when to file and open its tool calls.

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

**How did you choose the model?** By capability: gpt-4.1 handles text and images and structured output, and Content Understanding needs gpt-4.1, gpt-4.1-mini and text-embedding-3-large deployed. An embedding model turns text into numbers for similarity; it does not write text.

**Deployment options and configuration?** A model must be deployed to a Foundry resource before it can be called; the deployment has a name, a model and a capacity type, and availability depends on the region. I created mine with `tools.deploy_models` through the Azure CLI.

**Which AI workloads does Tarikh use?** Information extraction (Content Understanding), text analysis (PII), speech recognition and synthesis (Azure Speech), generative AI (brief), agentic AI (the two-tool agent), and a little computer vision (cheque image observations).

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

**Why Southeast Asia?** I checked Microsoft Learn for the Foundry project, Content Understanding, Speech fast transcription, neural voices, the Agent Service and gpt-4.1. Southeast Asia had all of them. Central India lacked Content Understanding and the Agent Service.

**Why Entra ID and no keys?** `az login` and `DefaultAzureCredential` mean no secret sits in a file or a repository. The roles needed are Cognitive Services User and Foundry User.

**What is record and replay for?** Every Azure call passes through a recorder. In replay mode it serves recorded responses and the page shows a banner, so the project can be shown without a connection without pretending that the answers are live.

**Why no front-end framework?** The interface is a few hundred lines of plain HTML, CSS and JavaScript. No build step means nothing extra to break on the day.

**Why does the interface look like paper?** The theme is "exact, accountable, docket". Three colours carry meaning (red for a deadline, green for checked by a person, blue for where something came from), and every status also has a word.

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
