"""Text of the report. Rendering is in build_report.py.

Markup inside strings:  {c:key} citation, {fig:key} {tab:key} cross-references, **bold**, *italic*, `code`.
Every number in Chapter 5 is read from report/build/metrics.json, which `python -m report.metrics` measures; none is typed in.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent

STUDENT = "Piyush Kumar Brahmbhatt"
UID = "24BAI70769"
CLASS = "24AML4 A"
PROGRAMME = "Computer Science and Engineering"
SPECIALIZATION = "Artificial Intelligence and Machine Learning"
DEGREE = "Bachelor of Engineering"          # wording follows the university template; see README for B.E. / B.Tech
LEADER = "Mr. Hari Haran"
LEADER_TITLE = "Program Leader (PL)"
START, END = date(2026, 7, 3), date(2026, 10, 31)
SUBMISSION = "November 2026"
TITLE = ("TARIKH: A LITIGATION PLATFORM FOR CHEQUE-BOUNCE (SECTION 138) CASES BUILT ON MICROSOFT AZURE AI, "
         "THAT READS THE PAPERS, COUNTS EVERY DEADLINE IN CODE AND KEEPS A PERSON IN CHARGE")

ABBREVIATIONS = [
    ("AI", "Artificial Intelligence"), ("AIML", "Artificial Intelligence and Machine Learning"),
    ("API", "Application Programming Interface"), ("CLI", "Command-Line Interface"),
    ("CSV", "Comma-Separated Values"), ("CU", "Content Understanding (Azure)"), ("Entra ID", "Microsoft Entra ID, the Azure sign-in service"),
    ("JSON", "JavaScript Object Notation"), ("JSONL", "JSON Lines, one JSON record per line"),
    ("NI Act", "Negotiable Instruments Act, 1881"), ("PII", "Personally Identifiable Information"),
    ("RBI", "Reserve Bank of India"), ("REST", "Representational State Transfer"),
    ("SDK", "Software Development Kit"), ("SQL", "Structured Query Language"),
    ("STT", "Speech to Text"), ("TPM", "Tokens Per Minute, the unit of model quota"), ("TTS", "Text to Speech"), ("UI", "User Interface"), ("UID", "Unique Identification number"),
    ("WCAG", "Web Content Accessibility Guidelines"),
]

REFERENCES = {
    "nia": "The Negotiable Instruments Act, 1881 (Act 26 of 1881), Chapter XVII, Sections 138 to 142, Government of India, "
           "Department of Financial Services, https://financialservices.gov.in/beta/sites/default/files/2022-10/1.%20Negotiable%20Instrument%20Act,%201881.pdf (accessed 20 November 2026).",
    "rbi": "Business Standard, \"After 3 months from issue date, cheques won't be accepted: RBI,\" 7 November 2011, "
           "https://business-standard.com/article/finance/after-3-months-from-issue-date-cheques-won-t-be-accepted-rbi-111110700057_1.html (accessed 20 November 2026).",
    "ipl": "iPleaders, \"Section 138 of the Negotiable Instruments Act, 1881,\" https://blog.ipleaders.in/section-138-of-negotiable-instruments-act-1881/ (accessed 20 November 2026).",
    "exam": "Microsoft Learn, \"Study guide for Exam AI-901: Microsoft Azure AI Fundamentals,\" skills measured as of 15 April 2026, "
            "https://learn.microsoft.com/credentials/certifications/resources/study-guides/ai-901 (accessed 20 November 2026).",
    "rai": "Microsoft, \"Responsible AI principles and approach,\" https://www.microsoft.com/en/ai/principles-and-approach (accessed 20 November 2026).",
    "cu": "Microsoft Learn, \"Azure Content Understanding in Foundry Tools: overview,\" https://learn.microsoft.com/azure/ai-services/content-understanding/overview (accessed 20 November 2026).",
    "cu2": "Microsoft Learn, \"Create a custom analyzer using REST APIs (Content Understanding),\" https://learn.microsoft.com/azure/ai-services/content-understanding/tutorial/create-custom-analyzer (accessed 20 November 2026).",
    "pii": "Microsoft Learn, \"What is Personally Identifiable Information (PII) detection in Azure AI Language?\" https://learn.microsoft.com/azure/ai-services/language-service/personally-identifiable-information/overview (accessed 20 November 2026).",
    "fn": "Microsoft Learn, \"Use function calling with Microsoft Foundry agents,\" https://learn.microsoft.com/azure/foundry/agents/how-to/tools/function-calling (accessed 20 November 2026).",
    "reg": "Microsoft Learn, \"Agent Service limits, quotas and region availability,\" https://learn.microsoft.com/azure/foundry/agents/concepts/limits-quotas-regions (accessed 20 November 2026).",
    "spreg": "Microsoft Learn, \"Azure Speech in Foundry Tools regions,\" https://learn.microsoft.com/azure/ai-services/speech-service/regions (accessed 20 November 2026).",
    "curg": "Microsoft Learn, \"Content Understanding language and region support,\" https://learn.microsoft.com/azure/ai-services/content-understanding/language-region-support (accessed 20 November 2026).",
    "sk": "Sudesh Kumar v. State of U.P. and another, High Court of Judicature at Allahabad, decided 1 March 2024 (2024 AHC 38337), "
          "https://www.foxmandal.in/wp-content/uploads/2024/04/Sudesh-Kumar-v.-State-of-U.P.-and-another.pdf (accessed 20 November 2026).",
    "ftcost": "Microsoft Learn, \"Fine-tuning cost management (Microsoft Foundry),\" deployment types and charges for fine-tuned models, https://learn.microsoft.com/azure/foundry/openai/how-to/fine-tuning-cost-management (accessed 21 November 2026).",
    "fttest": "Microsoft Learn, \"Deploy a fine-tuned model for testing (Developer tier),\" https://learn.microsoft.com/azure/ai-services/openai/how-to/fine-tune-test (accessed 21 November 2026).",
    "dep": "Microsoft Learn, \"Create model deployments in Microsoft Foundry,\" https://learn.microsoft.com/azure/foundry/foundry-models/how-to/create-model-deployments (accessed 20 November 2026).",
}

# --------------------------------------------------------------------------- measured numbers
def metrics() -> dict:
    return json.loads((HERE / "build" / "metrics.json").read_text())


def test_total(m: dict) -> int:
    t = m["tests"]
    return t["server"] + t["desk_browser"] + t["site_browser"] + t["engine_js"]


def abstract() -> list[str]:
    m = metrics()
    t = m["tests"]
    desk_ms = list(m["latency_ms"].values())[1]
    return [
        "A cheque returned unpaid can become a criminal complaint under Section 138 of the Negotiable Instruments Act, "
        "but only if three steps are taken inside fixed periods, and each period starts when the previous one ends. "
        "Advocates' offices count these dates by hand from photographs, scanned memos and phone calls, and a miscount can end the case.",
        "This report describes Tarikh, a litigation platform for these cases built during the industrial internship on Microsoft Azure AI "
        "Fundamentals (AI-901). Advocates, lenders and businesses create an account and keep their matters on a server. It reads the cheque, the bank's return memo and the demand notice with a Foundry vision model fine-tuned on labelled sample papers, or with Azure Content Understanding where the region offers it; "
        "transcribes a client's voice note with Azure Speech and masks personal details with Azure AI Language before any language "
        "model sees the text; lets an advocate check each reading against the paper; counts the four statutory periods in ordinary tested code, not in a model; "
        "drafts a brief in which every sentence cites a fact or is dropped; answers questions through a Foundry agent limited to two read-only tools; "
        "releases the brief only after a named advocate approves it; and keeps each matter's hearings, drafts, settlement and audit trail. "
        "Lenders can import a bank return file and see their whole portfolio by stage, the measures the Supreme Court asked trial courts to track in 2025.",
        "The platform is deployed in a Microsoft Foundry project in Korea Central, the one region that both the Azure for Students policy and the services' region lists leave open. "
        f"It passes {test_total(m)} automated checks: {t['server']} server checks, {t['desk_browser'] + t['site_browser']} browser checks and {t['engine_js']} checks of the browser's deadline engine, "
        f"one of which signs up and works a matter end to end against a running server. The engine counts a matter's four periods in about {m['engine_us_per_matter']:.0f} microseconds, "
        f"and a desk of {m['desk_matters']} matters loads in a median of {desk_ms:.0f} ms. "
        "The main conclusion is that the Azure services were useful for reading and drafting, while the parts that carry legal risk "
        "were safest as plain code with a person's approval at the end.",
    ]


KEYWORDS = ("Microsoft Azure AI Fundamentals, AI-901, Microsoft Foundry, fine-tuning, Azure Speech, Azure AI Language, Foundry Agent Service, "
            "responsible AI, Negotiable Instruments Act Section 138, deadline calculation")

# --------------------------------------------------------------------------- weekly diary
WEEKS = [
    ("AI workloads and the AI-901 skills outline",
     ["Read the AI-901 skills-measured outline and listed the six areas to cover over the internship.",
      "Studied the common AI workloads: generative and agentic AI, text analysis, speech, vision and information extraction.",
      "Wrote one-paragraph notes on each workload with an everyday example.",
      "Compared the old fundamentals outline with the AI-901 outline to see what moved to Foundry.",
      "Drew a map of the services against the outline to use as a revision sheet."],
     "AI-901 is built around building with Foundry, so each service has to be understood by what it does in an application."),
    ("Principles of responsible AI",
     ["Studied the six principles: fairness, reliability and safety, privacy and security, inclusiveness, transparency, accountability.",
      "Took notes on fairness considerations and where bias can enter a data set.",
      "Took notes on reliability and safety, and on privacy and security.",
      "Took notes on inclusiveness, transparency and accountability.",
      "Wrote a one-page checklist of questions to ask of any AI feature."],
     "Each principle turns into a question that can be asked of a design before any code is written."),
    ("How generative AI models work",
     ["Studied tokens, context windows and how a language model produces text one token at a time.",
      "Studied prompts: system and user messages, and why wording changes the answer.",
      "Studied configuration parameters such as temperature and maximum tokens.",
      "Practised writing the same instruction three ways and compared the outputs.",
      "Summarised why a model's arithmetic cannot be trusted for exact dates."],
     "A model predicts likely text; it does not calculate, so exact work belongs in code."),
    ("Choosing and deploying a model",
     ["Studied how to pick a model by capability: text, multimodal, reasoning and embedding models.",
      "Studied deployment options and why a deployment type depends on region.",
      "Created a Foundry project and checked region availability for each service on Microsoft Learn.",
      "Tried a model in the Foundry portal playground and compared the deployment types.",
      "Recorded the region choice and the reasons in a short note."],
     "Region decides which services and models can be used together, so it has to be chosen first."),
    ("Prompts and a chat client with the Foundry SDK",
     ["Wrote system prompts with rules, an output format and a refusal clause.",
      "Set up sign-in with Microsoft Entra ID through the Azure CLI instead of keys.",
      "Wrote a small chat client that sends a prompt to a deployed model and prints the reply.",
      "Added structured output so that the reply is JSON that a program can check.",
      "Wrote tests that run the client against a stand-in for the service."],
     "Sign-in without stored keys and structured output both make an application easier to defend."),
    ("Agents in Foundry",
     ["Studied what an agent is: a model, instructions and tools.",
      "Created a single agent in the Foundry portal and tested it with sample questions.",
      "Studied function calling: the agent asks, the application runs the function.",
      "Wrote a client that creates an agent and runs a tool loop.",
      "Noted that a tool should be small, read-only and tied to the data it may see."],
     "An agent is only as safe as the tools it is handed."),
    ("Text analysis",
     ["Studied keyword extraction, entity detection, sentiment analysis and summarisation.",
      "Called Azure AI Language from Python for entity detection.",
      "Studied PII detection and redaction and the categories it returns.",
      "Compared masked and unmasked output on invented sample sentences.",
      "Noted where redaction can miss a value and what to do about it."],
     "Masking is a safeguard, not a guarantee, and the application has to say so."),
    ("Speech recognition and synthesis",
     ["Studied speech to text and text to speech, and the difference between real-time and fast transcription.",
      "Transcribed short recordings with Azure Speech.",
      "Checked which locales are offered, including Hindi and Punjabi.",
      "Generated spoken output with a neural voice and listened for clarity.",
      "Noted that a locale must be chosen explicitly and cannot always be guessed."],
     "Language support differs by feature and region, so it must be checked rather than assumed."),
    ("Vision and image generation",
     ["Studied computer vision tasks: classification, detection and reading text from images.",
      "Sent an image to a multimodal model together with a prompt.",
      "Studied image generation and where it is and is not appropriate.",
      "Built a small client that asks a multimodal model what is visible on a picture.",
      "Noted that the model should describe what it sees and not judge it."],
     "A multimodal model is good at describing a picture and weak at deciding what the picture means legally."),
    ("Content Understanding",
     ["Studied information extraction from documents, images, audio and video.",
      "Studied prebuilt and custom analyzers and the fields a custom analyzer defines.",
      "Read how analyzers depend on model deployments in the Foundry resource.",
      "Worked through the custom-analyzer exercise and studied a result with its confidence and location.",
      "Noted that every extracted field comes with a place on the page that can be shown to a person."],
     "Location and confidence turn an extraction into something a person can check."),
    ("Choosing the project and reading the law",
     ["Listed project ideas against the AI-901 areas and the daily needs of a professional.",
      "Chose a law-office desk for cheque-bounce cases and read Section 138 and the connected sections.",
      "Read published worked examples of how the periods are counted.",
      "Wrote the problem statement, the users and the list of requirements.",
      "Drew the first architecture and decided to keep the arithmetic out of the model."],
     "The statute has four dependent clocks, which is exactly the part a model should not count."),
    ("Deadline engine",
     ["Wrote the tests for month-end, leap-year and missing-date cases first.",
      "Implemented the four windows: validity, notice, payment and complaint.",
      "Decided that the earlier date is shown when readings differ and that holidays are left to the advocate.",
      "Reworded the drawer's fifteen days as Running or Ended because that clock belongs to the other side.",
      "Ran the full test set and fixed one boundary case."],
     "Writing the tests before the code found the month-end case before it could reach a user."),
    ("Reading the papers",
     ["Defined the fields for the cheque, the return memo and the demand notice.",
      "Wrote the Content Understanding analyzer definitions and the deployment settings they need.",
      "Stored each reading as a fact with its page region and confidence.",
      "Made three fields manual because they are not printed on any paper.",
      "Drew sample papers with a script so that no real person's cheque is used."],
     "Three of the dates that matter are not on any paper, so the desk has to ask for them."),
    ("Voice notes and masking",
     ["Added a voice note upload with an explicit locale.",
      "Added masking of the transcript with Azure AI Language.",
      "Kept both the original and the masked transcript and decided that only the masked one may go to the model.",
      "Showed the two side by side in the interface with the masked words marked.",
      "Added checks on file type and size."],
     "The order of the steps is the safeguard: transcribe, mask, then reason."),
    ("Drafting the brief",
     ["Wrote the prompt and a schema in which every claim carries fact identifiers.",
      "Wrote the check that drops a claim with no source or an unknown source.",
      "Showed each claim with a source chip that opens the page region.",
      "Added the approval step with a reviewing advocate's name and an audit entry.",
      "Allowed reading aloud only after approval."],
     "A sentence that cannot point to a fact is removed, not softened."),
    ("Agent with two tools",
     ["Wrote the two read-only tools: one for deadlines and one for facts.",
      "Bound the tools to a single matter so that the agent cannot see another.",
      "Started a fresh conversation for every question so that no earlier answer leaks.",
      "Added a limit on tool rounds and showed the tool calls beside the answer.",
      "Added record and replay so that the application can be shown without a live connection."],
     "Showing the tool calls beside the answer lets a reader see where each fact came from."),
    ("Interface and accessibility",
     ["Chose the visual language: paper, ink and three colours that each carry one meaning.",
      "Built the deadline clock with a draggable and keyboard-operable marker for today.",
      "Added a text table that gives the same dates as the clock.",
      "Checked contrast values and ran an automated accessibility check.",
      "Checked the layout at phone width and fixed the overflow."],
     "A colour is only used when it also has a word beside it."),
]
CLOSING_DAY = ("Ran the full test set, read the report against the university format and prepared the viva notes.", "30 Oct")

# --------------------------------------------------------------------------- chapters
def chapters(deadline_rows: list[list[str]], worked_rows: list[list[str]]) -> list[tuple]:
    m = metrics()
    t = m["tests"]
    lat_rows = [[k, f"{v:.1f} ms"] for k, v in m["latency_ms"].items()] + [["Count the four periods of one matter (deadline engine, mean of 10,000 runs)", f"{m['engine_us_per_matter']:.1f} µs"]]
    loc_rows = [[k, f"{v:,}"] for k, v in m["loc"].items()] + [["**Total**", f"**{sum(m['loc'].values()):,}**"]]

    C: list[tuple] = []
    add = C.append

    # ------------------------------------------------------------------ 1
    add(("h1", "Introduction"))
    add(("h2", "Topic addressed"))
    add(("p", "A cheque that comes back unpaid because the account has too little money is not only a civil debt. Under Section 138 of the "
              "Negotiable Instruments Act, 1881 {c:nia} it is an offence, provided three things happen in order. The cheque must be presented to "
              "the bank within three months of its date, which is the validity period the Reserve Bank of India has applied since 1 April 2012 {c:rbi}. "
              "The payee must then send a written demand within 30 days of learning that the cheque was returned. And the drawer must fail to pay "
              "within 15 days of receiving that demand. Only after that may the payee complain to a Magistrate, and the complaint must be made within one month "
              "of the day the 15 days end {c:nia}{c:ipl}."))
    add(("p", "Each period starts from a date that the earlier step creates, and two of those dates, the day the memo reached the payee and the day the "
              "drawer received the notice, are not printed on any paper. In a small advocate's office they are worked out by hand from a photograph of the cheque, "
              "a scanned bank memo and what the client says on the telephone. This report describes **Tarikh** (Hindi for \"date\"), a case desk for one such "
              "matter at a time. It reads the papers, asks for the missing dates, counts the four periods, drafts a short brief for the advocate, "
              "and answers questions about the matter."))
    add(("h2", "Importance and novelty of the problem"))
    add(("p", "A wrong count costs the client, so this is a fair test of whether Azure AI services can be used responsibly where a mistake is not an inconvenience. The AI-901 course teaches each service separately {c:exam}. "
              "What this project adds is a way of joining them under rules that a professional can check. Four decisions shape everything that follows."))
    add(("bul", ["**Dates are counted by code, not by a model.** A language model predicts text; it does not calculate. The counting is ordinary Python with boundary tests.",
                 "**A sentence with no source is removed.** Every claim in a drafted brief must name the facts it relies on. A claim with none, or with an unknown one, is dropped and listed.",
                 "**Personal details are masked before reasoning.** A voice note is transcribed and masked, and only the masked text goes to the language model.",
                 "**A named advocate approves.** Nothing is read aloud to a client until an advocate has approved the brief, and the approval is written to an audit trail."]))
    add(("h2", "Related work"))
    add(("p", "The law itself is the first source: the Act sets the conditions {c:nia}, the Reserve Bank's circular sets the validity of a cheque {c:rbi}, "
              "and published commentary explains how the periods follow one another {c:ipl}. Worked examples of the counting are used in this report as test cases (Section 5.2), "
              "not as the project's own results. On the Azure side the project follows the documented patterns: custom analyzers in Content Understanding {c:cu}{c:cu2}, "
              "personal-data detection in Azure AI Language {c:pii}, function calling for Foundry agents {c:fn}, and Microsoft's six principles of responsible AI {c:rai}. "
              "Nothing in this report is legal advice."))
    add(("h2", "Objectives and scope"))
    add(("p", "The objectives, to which Chapter 6 returns, were as follows."))
    add(("bul", ["**O1.** Use each AI-901 area on a real Azure service in one working application.",
                 "**O2.** Count the Section 138 periods correctly and show them clearly, without guessing a missing date.",
                 "**O3.** Draft a brief that a reader can trace, line by line, to the papers.",
                 "**O4.** Keep personal details away from the reasoning model and keep a person in charge of the result.",
                 "**O5.** Make the desk usable by an advocate on a laptop or a phone, with the keyboard, and in more than one language."]))
    add(("p", "Within scope are accounts and sessions, matters kept per account, three papers per matter, a voice note in English, Hindi or Punjabi where the Speech service offers it, "
              "four periods, seven drafts, one brief, one agent, a hearing diary, a settlement record, return-file import for lenders and a public deadline checker. "
              "Out of scope are legal advice, filing, a calendar of court holidays, delay condonation, payments, password reset and production hosting. "
              "All names in the sample matters are fictional."))
    add(("h2", "Organisation of the report"))
    add(("p", "Chapter 2 is the weekly record. Chapter 3 gives the requirements and design, Chapter 4 the implementation, Chapter 5 testing, results and the responsible-AI review, "
              "and Chapter 6 the conclusions. The appendices hold the AI-901 syllabus, the course certificate, the screens of the working platform, the record of the Azure deployment and the commands for running the project."))

    # ------------------------------------------------------------------ 2
    add(("h1", "Weekly Report"))
    add(("p", "The internship ran from 3 July to 31 October 2026. The record below follows the university's weekly format: five working days at a time, "
              "the topic of the week, what was done each day, and what was learned. Working days are Monday to Friday."))
    add(("weeks",))

    # ------------------------------------------------------------------ 3
    add(("h1", "Requirements and Design"))
    add(("h2", "Requirements"))
    add(("p", "The users are advocates and their juniors who handle cheque-bounce complaints. The requirements in {tab:req} came from reading the statute and from the question "
              "\"what would make this safe to rely on?\" The last column says how each one is checked."))
    add(("table", "req", "Requirements and how each is verified",
         ["ID", "Requirement", "Checked by"],
         [["R1", "Count the validity, notice, payment and complaint periods in code from dates that a person has entered or confirmed.", "Deadline tests (Chapter 5)"],
          ["R2", "Never guess a missing date; say which date is missing.", "Deadline tests; browser test"],
          ["R3", "Read the cheque, memo and notice into labelled facts and show where on the page each was read.", "Extraction tests; live run"],
          ["R4", "Let the advocate correct or confirm any fact; record corrections.", "API tests; audit trail"],
          ["R5", "Transcribe a voice note and mask personal details before any reasoning step.", "Redaction and API tests"],
          ["R6", "Make every claim in the brief cite facts; drop any that do not.", "Reasoning tests"],
          ["R7", "Answer questions through an agent limited to two read-only tools for one matter.", "Agent tests"],
          ["R8", "Release the brief and the spoken version only after a named advocate approves.", "API and browser tests"],
          ["R9", "Sign in with Entra ID; keep no keys in files.", "Configuration tests; service checker"],
          ["R10", "Work at phone width, by keyboard, and without relying on colour alone.", "Browser and accessibility checks"],
          ["R11", "Let a person create an account, sign in and out, and see only their own matters.", "Account tests; end-to-end browser test"],
          ["R12", "Keep hearings, settlements, draft approvals and imported matters, and log every change.", "Desk API tests; end-to-end browser test"]],
         [0.5, 3.9, 1.5]))
    add(("h2", "Architecture"))
    add(("p", "The system is one FastAPI server and the pages it serves. A person signs up or signs in; the server keeps users, sessions, matters and the audit trail in SQLite, "
              "and sends each request that needs Azure to a pipeline. The pipeline uses the deadline engine and a recorder that sits in front of every Azure call, as shown in {fig:arch}. "
              "The website and the desk are generated from templates by one script into plain HTML, one stylesheet and three scripts; the same deadline rules run in the browser for instant feedback. The deliberate choice was to put the steps in ordinary code, "
              "in order, and call a service at each step, rather than to hand the whole job to one agent. That keeps every step testable and keeps the legal arithmetic out of any model."))
    add(("fig", "arch", "fig_architecture.png", "Architecture of Tarikh. The heavy box is plain code; the dashed boxes are where the system leaves the laptop.", 5.2))
    add(("h2", "Workflow"))
    add(("p", "{fig:flow} shows the six steps of a matter. Two are human decisions: the advocate checks the readings, and the advocate approves the brief. "
              "The counting step is plain code. A voice note, if there is one, joins at the drafting step only in masked form."))
    add(("fig", "flow", "fig_workflow.png", "The six steps of a matter. Shaded steps are decisions taken by a person.", 5.4))
    add(("h2", "Choice of Azure services"))
    add(("p", "Each service was chosen for one job and tied to the AI-901 skill it exercises {c:exam}, as in {tab:svc}. The student subscription permits a fixed list of regions: "
              "Central India, East Asia, Korea Central, UAE North and Indonesia Central. Of these, Korea Central and UAE North offer the Foundry Agent Service {c:reg}, Speech lists Korea Central among its regions {c:spreg}, and none offers "
              "Content Understanding, which is listed in twelve other regions {c:curg}. Tarikh is therefore deployed in **Korea Central**. "
              "A second limit appeared on the quota page: the student subscription has no quota in Korea Central for any base chat model, so a deployment of gpt-4.1 is refused, "
              "but it does have quota for fine-tuned gpt-4.1-mini on the Developer tier. The model behind Tarikh is therefore gpt-4.1-mini fine-tuned on labelled sample papers (Section 4.9). "
              "It fills the same fields through a strict JSON schema; because that reading carries no location on the page, every value it returns is flagged for the advocate to check "
              "against the paper. The Content Understanding reader remains in the code and is selected by one setting where the region allows it (decision record 0006)."))
    add(("table", "svc", "Services, their job in Tarikh and the AI-901 skill covered",
         ["Service", "Job in Tarikh", "AI-901 skill area"],
         [["Fine-tuned gpt-4.1-mini with vision (Korea Central); Content Understanding where offered", "Reads the cheque, return memo and demand notice into fields; Content Understanding adds confidence and page location", "Extract information from documents and forms"],
          ["Azure AI Language (PII redaction)", "Masks personal details in the voice-note transcript", "Build an application that includes text analysis"],
          ["Azure Speech", "Fast transcription of a voice note; neural voice for reading the approved brief", "Build an application by using Azure Speech"],
          ["Foundry model deployment (tarikh-reader)", "Drafts the brief; notes what is visible on a cheque image", "Chat client with the Foundry SDK; interpret visual input; fine-tuning"],
          ["Foundry Agent Service", "Answers questions with two read-only tools", "Create and test a single-agent solution; client for an agent"],
          ["Responsible AI principles", "Design review of every feature (Chapter 5)", "Describe principles of responsible AI"]],
         [1.7, 2.6, 1.6]))
    add(("h2", "Data model"))
    add(("p", "A matter owns its documents, an optional transcript, a brief and an append-only audit trail. A document holds facts, and each fact keeps its value, its confidence and the page region it was read from. "
              "A claim in the brief stores the identifiers of the facts it cites, which is what makes the source rule in R6 checkable ({fig:data})."))
    add(("fig", "data", "fig_datamodel.png", "Data model. Every claim in a brief points to facts; every fact points to where it was read.", 4.6))
    add(("h2", "Interface design"))
    add(("p", "The visual idea is the Indian tear-off wall calendar, because a cheque case is a sequence of dates. The mark is a red calendar leaf with two binding rings and the Devanagari ता; "
              "the leaf itself, with its red month band, black numeral and Hindi weekday, is the recurring object on every page and in the desk. "
              "The palette is black, white and one calendar red; amber means a person must act, green means settled or approved, and nothing else is coloured. "
              "Text is set in Schibsted Grotesk, calendar numerals in Anton, case data in JetBrains Mono and Hindi in Tiro Devanagari, all held locally. "
              "Every status is written in words as well as shown in colour, every control works by keyboard, and all movement stops for people who ask their system to reduce motion."))
    add(("p", "The product is presented as four products on one engine: Desk for advocates, Recover for lenders, Check as a free public tool and an API for other systems. "
              "The home page shows the three papers of a case as they would lie on a desk, with the last day to file on a calendar leaf, before any feature is described ({fig:home})."))
    add(("fig", "home", "shot_home.png", "The home page: the three papers of a case, the date that matters, and the two ways in (screen capture).", 5.9))

    # ------------------------------------------------------------------ 4
    add(("h1", "Implementation"))
    add(("h2", "Deadline engine"))
    add(("p", "`app/deadlines.py` has one function, `compute_windows`, which takes up to five dates and the day being counted from, and returns four windows. "
              "The rules are in {tab:rules}. Three conventions were decided and written into the windows themselves, so that the screen states them. "
              "A month is counted to the day before the same calendar date, or to the last day of a shorter month. Where the two usual ways of ending a month differ by a day (the day before the same date, or the same date), the earlier is shown. "
              "And court holidays and condonation of delay are not applied, because they are for the advocate."))
    add(("table", "rules", "The four periods as implemented",
         ["Period", "Starts", "Ends", "Source"],
         [["Cheque validity", "Date on the cheque", "Three months later, day before the same date", "Proviso (a); RBI circular {c:rbi}"],
          ["Demand notice", "Memo received by payee", "30 days later", "Proviso (b) {c:nia}"],
          ["Drawer's time to pay", "Day after notice received", "15 days after receipt", "Proviso (c) {c:nia}"],
          ["Complaint", "Day after the 15 days end", "One month later", "Section 142(1)(b) {c:nia}"]],
         [1.4, 1.6, 1.7, 1.2]))
    add(("p", "The 15 days belong to the drawer, so the screen calls that period Running or Ended and never Missed. {tab:worked} and {fig:win} show a worked example computed by the engine "
              "for a fictional matter, counted from 21 November 2026."))
    add(("table", "worked", "Worked example from `compute_windows` (fictional matter, counted from 21 Nov 2026)",
         ["Period", "From", "To", "Status"], worked_rows, [2.2, 1.2, 1.2, 1.3]))
    add(("fig", "win", "fig_windows.png", "The four periods for the worked example. Light grey bars are met, the dark grey bar is the drawer's time, and red is the open complaint period.", 5.3))
    add(("h2", "Reading the papers"))
    add(("p", "Tarikh has two readers behind one interface, chosen by the setting `TARIKH_EXTRACTOR`. In Korea Central, where the project is deployed, the **model reader** sends the image of the paper "
              "to the model deployment with an instruction to return each field exactly as printed, dates as YYYY-MM-DD, and null where a field is not visible; the reply must match a strict JSON schema "
              "built from the same field list, so a value can never arrive in the wrong place. Each value is flagged \"read by the model without a location box\" until the advocate confirms it."))
    add(("p", "Where Content Understanding is offered, the **analyzer reader** is used instead. Three custom analyzers extend the prebuilt document analyzer {c:cu2}, one for each paper. Content Understanding needs model deployments in the Foundry resource, "
              "so the program first sets the resource's default deployments, gpt-4.1, gpt-4.1-mini and text-embedding-3-large, once per run, and then creates the analyzer if it is not already there. "
              "{tab:fields} lists the fields. Each extracted value is stored with its confidence and its polygon on the page. "
              "A low confidence is flagged in words, and \"Show on paper\" outlines the region so that the advocate can compare it with the original. "
              "Fields that appear on no paper are marked manual and are entered by the advocate."))
    add(("table", "fields", "Fields read from each paper (manual fields are entered by the advocate)",
         ["Paper", "Fields read from the paper", "Manual"],
         [["Cheque", "Cheque number, date, amount in figures, drawer, payee, drawee bank", "None"],
          ["Return memo", "Cheque number, presented on, returned on, reason for return", "Memo received by payee"],
          ["Demand notice", "Cheque number, notice dated, amount demanded", "Notice posted on; notice received by drawer"]],
         [1.3, 3.0, 1.6]))
    add(("p", "No real person's cheque was used at any stage. The three papers in {fig:papers} are drawn by a script, `tools/make_samples.py`, which can also vary the names, amounts and dates "
              "and age the paper into a phone photograph with tilt, shadow and blur. These are the papers used for the tests, the sample matters and the training data in Section 4.9."))
    add(("fig", "papers", "fig_papers_bw.png", "The three fictional sample papers: cheque, bank return memo and demand notice, drawn by the project's own script.", 5.9))
    add(("p", "When a cheque is supplied as an image, the Foundry model is also asked to note whether a signature, date, payee, amount in words and an account-payee crossing are present, absent or unclear. "
              "It is told to describe only what it sees and not to judge validity."))
    add(("h2", "Voice notes and masking"))
    add(("p", "A voice note is uploaded or recorded, and its type is decided from its bytes, not from its file name. Azure Speech fast transcription is called with one explicit locale, English, Hindi or Punjabi, "
              "because the service is given one language to expect and the advocate knows which was spoken. The transcript is passed to Azure AI Language for PII redaction {c:pii}. "
              "The original and the masked text are both stored, shown side by side with masked words marked, and only the masked text is passed to the reasoning step."))
    add(("h2", "The brief and the source rule"))
    add(("p", "The Foundry model is called through the responses API with a system prompt, a statute digest, the facts and the masked transcript, and must reply in a fixed JSON schema in which each claim has a section, "
              "text and a list of fact identifiers. `validate_brief` then keeps a claim only if it cites at least one identifier and every identifier exists. "
              "Others are dropped, and a line saying why is added to a list shown under the brief. "
              "In the interface each kept claim carries chips such as \"Cheque · Date on cheque · 20 Sep 2026\" that open the page region. "
              "The advocate types a name and approves; the approval and the name are written to the audit trail, and only then is \"Read to the client\" enabled."))
    add(("h2", "Agent with two tools"))
    add(("p", "Questions go to a Foundry agent defined with a prompt-agent definition and two function tools, `get_deadlines` and `get_fact` {c:fn}. "
              "Both are read-only and are bound to the one matter being asked about. The application runs the tool when the agent asks and returns the result, "
              "up to a fixed number of rounds. Each question starts a fresh conversation, so nothing from an earlier answer is carried over. "
              "The agent's rules, in `system_agent.md`, forbid calculating a date, require the earlier date to be called the safer one, and require missing values to be named and not filled in. "
              "The tool calls are shown in a disclosure under each answer."))
    add(("h2", "Recording, replay and errors"))
    add(("p", "Every call to Azure passes through a recorder. In live mode it records the request and response into a cassette; in replay mode, set by `TARIKH_MODE=replay`, it serves them back and the page shows a banner saying so. "
              "This allows the project to be shown and tested without a connection, without pretending that replayed answers are live. "
              "Service errors are turned into plain sentences that say what failed and what to do next, for example a missing role assignment or an unsupported file type."))
    add(("h2", "Accounts and sessions"))
    add(("p", "A person signs up with a name, an email address, a password and the kind of work they do. The password is hashed with scrypt from Python's standard library, with a random salt, "
              "and compared in constant time; the password itself is never stored. Signing in issues a random 32-byte token in an HttpOnly cookie that lasts fourteen days, and signing out deletes it. "
              "A middleware refuses every data route without a valid session, and every matter carries its owner, so a request for another person's matter answers as if it did not exist ({fig:signup})."))
    add(("fig", "signup", "shot_signup.png", "Creating an account (screen capture).", 5.6))
    add(("h2", "The desk"))
    add(("p", "The desk is where the work happens. Today lists what runs out first: complaint and notice deadlines in order of days left, hearings in the next three weeks, drafts waiting for approval and dates that no paper shows ({fig:desk}). "
              "Each matter page holds the moveable clocks, the papers with their facts, the hearing diary with a form to record what happened and fix the next date, seven sourced drafts, "
              "the AI brief, the agent, the settlement calculator and the activity log ({fig:matter}). A command palette (Ctrl K) finds any matter or page. "
              "The sidebar folds into a rail of icons and a marker slides to the item under the pointer; at phone width it becomes a sheet ({fig:phone})."))
    add(("fig", "desk", "shot_desk.png", "Today: deadlines in order of urgency, the week's hearings and what is waiting for the advocate (screen capture).", 5.9))
    add(("fig", "matter", "shot_matter.png", "One matter: the last day to file, the clocks and the dates that set them (screen capture).", 5.9))
    add(("p", "For lenders, the portfolio view groups every matter by stage, totals the money at stake and recovered, counts adjournments per filed case and ages the filed cases, "
              "which are the measures the Supreme Court asked trial courts to track in Sanjabij Tari v. Kishore S. Borcar (2025). A bank return file in CSV opens one matter per row; "
              "a row with a date that is not a real date is skipped and reported, never repaired. Selected matters can be allocated to a panel advocate in one step ({fig:portfolio})."))
    add(("fig", "portfolio", "shot_portfolio.png", "The portfolio after importing the sample return file (screen capture).", 5.9))
    add(("fig", "phone", "shot_phone.png", "Today at phone width (screen capture).", 2.2))
    add(("h2", "Deployment on Azure for Students"))
    add(("p", "The project runs on the student's own Azure for Students subscription, created with the university account 24BAI70769@cuchd.in. The subscription carries a policy that allows resources "
              "in only five regions, Central India, East Asia, Indonesia Central, Korea Central and UAE North; every other region, South India included, was refused at creation. "
              "Inside it, one resource group, `tarikh-rg` in Korea Central, holds the Foundry resource `tarikh-24bai70769` and the Foundry project `tarikh` ({fig:azure}). "
              "Azure Speech and Azure AI Language are reached through the same resource, so a single sign-in covers every service."))
    add(("fig", "azure", "fig_azure.png", "Where Tarikh lives in Azure, and the path the paper reader takes from labelled data to a deployment.", 5.6))
    add(("p", "The quota page for Korea Central showed 0 tokens per minute for every base chat model offered to the subscription, including gpt-4.1, gpt-4o and the o-series, and the portal refused a "
              "gpt-4.1 deployment for insufficient quota (Appendix D). The same page showed 500,000 tokens per minute for fine-tuned gpt-4.1-mini on the Developer tier. "
              "Microsoft's documentation describes that tier as charging per token with no hourly hosting fee, without an availability guarantee, and with a deployment that lasts 24 hours {c:ftcost}{c:fttest}. "
              "That fits a teaching project well: nothing is charged while the desk is idle, and the deployment is renewed on the days the desk is used."))
    add(("p", "The training data are written by `tools/make_finetune.py` from the sample-paper script. Ten fictional cases give 30 training papers, half of them aged into phone photographs, and three further cases give "
              "9 validation papers that the model never trains on ({tab:ft}). Each example pairs the image of one paper with the instruction the desk itself sends and the exact answer expected, "
              "in the JSON Lines chat format that Foundry fine-tuning accepts. Training uses the supervised method with global training, and the trained model is deployed under the name `tarikh-reader`, "
              "which is the only value the desk needs in its settings."))
    add(("table", "ft", "Training data for the paper reader (all papers fictional)",
         ["Set", "Cases", "Papers", "Labelled fields", "Purpose"],
         [["Training", "10", "30", "130", "Teach the model the papers' layout and the answer format"],
          ["Validation", "3", "9", "39", "Measure field accuracy on papers the model has not seen"]],
         [1.0, 0.7, 0.8, 1.2, 2.2]))
    add(("h2", "Sign-in and configuration"))
    add(("p", "The program uses `DefaultAzureCredential`, which means that `az login` is enough on a laptop and no key is written to any file. The person needs the Cognitive Services User and Foundry User roles on the resource. "
              "Settings such as the region, the endpoint and the deployment names are read from environment variables. A single command, `python -m tools.check_setup`, makes one real call to each service and prints a plain pass or fail with the fix; "
              "`python -m tools.deploy_models` creates the model deployments through the Azure CLI {c:dep}. Appendix E lists the commands."))

    # ------------------------------------------------------------------ 5
    add(("h1", "Testing, Results and Responsible AI"))
    add(("h2", "Test strategy"))
    add(("p", "Tests were written before the code for the deadline engine, the store and the configuration. Services that need Azure are tested against hand-written stand-ins that follow the same interface, "
              "so the logic around them, such as the source rule and the agent loop, is exercised on every run. {tab:tests} shows the layers. "
              f"The last run passed all {test_total(m)}: {t['server']} server checks, {t['desk_browser']} browser checks of the case desk, {t['site_browser']} browser checks of the website and platform, "
              f"and {t['engine_js']} checks of the deadline engine as it runs in the browser. "
              "One browser check starts a real server, signs up, loads the sample matters, enters a missing date, records a hearing, opens a matter, imports the sample return file, allocates the matters and signs out, "
              "and fails if the page raises any error on the way."))
    add(("table", "tests", "Automated checks by layer",
         ["Layer", "What it proves"],
         [["Deadline engine", "Month-end, leap-year, missing-date, window status and rule wording"],
          ["Store and API", "Persistence, fact validation, approval before speech, error messages, file-type sniffing"],
          ["Extraction, redaction, speech", "Mapping of service output into facts; masking; locale handling"],
          ["Reasoning and agent", "Source-or-drop rule; tool binding to one matter; tool-round limit"],
          ["Recorder and configuration", "Record and replay; required settings; model deployment plan"],
          ["Accounts and desk API", "Sign-up, sign-in, sign-out, isolation between accounts, entered dates, hearings, settlements, approvals, import"],
          ["Browser (Chromium)", "Live clocks, Check, calculator, ordering, drafts gate, allocation, command palette, links, no third-party requests, phone menu, reduced motion, the full account journey"]],
         [1.9, 4.0]))
    add(("h2", "Deadline checks"))
    add(("p", "The boundary cases in {tab:bound} are executed by the engine when this report is built, and the build stops if any result differs from the value shown. "
              "One row follows the dates recorded in a published High Court judgment {c:sk}; the others are checked by hand arithmetic."))
    add(("table", "bound", "Boundary cases for the deadline engine", ["Case", "Input", "Result"], deadline_rows, [2.2, 2.0, 1.7]))
    add(("h2", "Measured results"))
    add(("p", f"The figures in {{tab:perf}} were measured on {m['measured_on']} by `python -m report.metrics`, which starts the server, signs up, loads the {m['desk_matters'] - 24} sample matters, imports the "
              "24-row sample return file and times each request 25 times; the median is shown. Sign-up is the slowest step by design, because the password hash is made deliberately expensive. "
              "Counting the four periods of a matter takes microseconds, so the desk can recount every matter on every request instead of storing a date that might go stale."))
    add(("table", "perf", "Response times of the running server (median of 25 requests)", ["Operation", "Time"], lat_rows, [4.6, 1.3]))
    add(("p", f"The website and the desk are {m['site']['pages']} pages built from templates, with {m['site']['code_kb']} KB of HTML, CSS and JavaScript and {m['site']['fonts_kb']} KB of fonts held on the server, "
              f"so a page makes no request to any other website. The server offers {m['routes']} API routes. {{tab:loc}} gives the size of each part of the code base."))
    add(("table", "loc", "Size of the code base (non-blank lines)", ["Part", "Lines"], loc_rows, [4.6, 1.3]))
    add(("p", "The paper reader is measured differently, because its output is a model's reading and not a calculation. `python -m tools.evaluate_reader` sends each of the 9 validation papers "
              "to the deployed reader exactly as the desk does and compares every one of the 39 fields with the answer written for it, after removing spaces and punctuation. "
              "Whatever the score, the desk is built so that a misread value cannot reach a deadline unseen: every value read by the model is marked as such until an advocate confirms it, "
              "and a date that no paper shows is always asked for."))
    add(("h2", "Responsible AI review"))
    add(("p", "Each of Microsoft's six principles {c:rai} was turned into a question about a feature, and the answer was checked. {tab:rai} gives the result."))
    add(("table", "rai", "The six principles applied to Tarikh",
         ["Principle", "What the design does", "How it is checked"],
         [["Fairness", "Nothing scores, ranks or predicts a person; every matter gets the same arithmetic.", "Design review"],
          ["Reliability and safety", "Dates come from tested code; missing dates are named; low confidence is flagged in words.", "Deadline and extraction tests"],
          ["Privacy and security", "Transcripts are masked before reasoning; sign-in by Entra ID with no stored keys; file type and size are checked.", "Redaction, API and configuration tests"],
          ["Inclusiveness", "Voice in English, Hindi and Punjabi where offered; keyboard use; text equivalent of the clock; no colour-only status.", "Browser tests; accessibility scan"],
          ["Transparency", "Source chips, \"Show on paper\", visible tool calls and a banner in replay mode.", "Browser tests"],
          ["Accountability", "A named advocate approves; an audit trail records every change; deadlines are labelled for the advocate to confirm.", "API tests"]],
         [1.3, 3.3, 1.3]))
    add(("h2", "Limitations"))
    add(("bul", ["Masking covers the voice-note transcript. The extracted facts, which include the names of the parties, are passed to the reasoning model when a brief is drafted, so the desk should be used only with the client's permission.",
                 "PII detection can miss a value. The original transcript is therefore kept apart from the masked one, and the masked one is shown to the advocate.",
                 "Court holidays, delay condonation and the question of where a complaint may be filed are not computed.",
                 "The engine does not count the day of receipt of the notice, so a notice received on 8 January gives 15 days ending on 23 January, as in the judgment cited in Section 5.2. A court that counted the day of receipt as the first day would end every period one day sooner, and the desk would then show a date one day late. The advocate is told to confirm every date for this reason.",
                 "A PDF is read but is shown as a link, not in the viewer overlay; a phone photograph in HEIC format is refused with a message that says why.",
                 "Accounts have no password reset or email verification yet, and the server keeps everything in one SQLite file on one machine."]))

    # ------------------------------------------------------------------ 6
    add(("h1", "Conclusions and Recommendations"))
    add(("h2", "Conclusions"))
    add(("p", "Against the objectives in Chapter 1: **O1** was met, since the project uses a Foundry model deployment for reading papers and drafting, Azure AI Language, Azure Speech and the Foundry Agent Service, with a Content Understanding reader ready where the region offers it, "
              "which between them cover each implementation area of the AI-901 outline {c:exam}. **O2** was met by the deadline engine and its boundary tests, with the earlier date shown and no date assumed. "
              "**O3** was met by the source rule, which drops any claim without a cited fact. **O4** was met for transcripts and for approval, with the limitation on extracted facts stated in Section 5.5. "
              "**O5** was met in the interface, which was checked at phone width and by keyboard."))
    add(("p", "The most useful lesson was where not to use a model. Reading a handwritten or printed cheque and drafting a plain summary are tasks where the Azure services helped. "
              "Counting dates was safer as about a hundred lines of tested code, and the decision to release a brief was safer as a person's signature."))
    add(("h2", "Recommendations"))
    add(("bul", ["Add a court-holiday calendar for the relevant district, and show a second date for the advocate to choose when a deadline falls on a holiday.",
                 "Show both ways of counting the day of receipt side by side and mark the earlier one, so that the date shown is always the safer of the two.",
                 "Move to a managed database and to Microsoft Entra External ID for sign-in, with roles, so that a junior can draft and only a senior can approve.",
                 "Measure reading accuracy per field on real papers, used with the clients' permission; the training and validation papers are drawn by script, so they show that the method works, not how well it reads every bank's memo.",
                 "Move the reader from the Developer tier, whose deployment lasts 24 hours, to a standard deployment once quota is granted, so that it does not have to be renewed.",
                 "Compare the brief with advocates' own notes before any use outside a classroom.",
                 ]))
    add(("h2", "What the internship taught"))
    add(("p", "Studied one at a time, the services look interchangeable. Built together, each has a limit to design around: a region that lacks a service, "
              "a locale that cannot be guessed, a redaction that can miss, a model that cannot calculate. Putting those limits on the screen, and not only in the report, made the project honest."))
    return C


GALLERY = [
    ("g_menu", "g_menu.png", "Website: the Products menu unfolds into the four products and the way in.", 5.9),
    ("g_why", "g_why.png", "Website: the size of the problem, with each figure's source printed under it.", 5.9),
    ("g_directions", "g_directions.png", "Website: the Supreme Court's 2025 directions and what the platform does for each.", 5.9),
    ("g_platform", "g_platform.png", "Website: the platform page, one engine under every product.", 5.9),
    ("g_check", "g_check.png", "Check, the free public tool: the dates of a bounced cheque counted without an account.", 5.9),
    ("g_signin", "g_signin.png", "Signing in.", 5.9),
    ("g_empty", "g_empty.png", "A new account's first screen: open a matter or load the sample matters.", 5.9),
    ("g_rail", "g_rail.png", "Today with the sidebar folded into a rail of icons.", 5.9),
    ("g_palette", "g_palette.png", "The command palette (Ctrl K) finding a matter by the accused's name.", 5.9),
    ("g_matters", "g_matters.png", "Matters, ordered by what runs out first.", 5.9),
    ("g_dates", "g_dates.png", "A matter's moveable clocks: dragging a date shows what would change, and nothing is saved.", 5.9),
    ("g_papers", "g_papers.png", "Papers and facts for a matter without papers: upload a photo or scan, or record the client's account.", 5.9),
    ("g_hearings", "g_hearings.png", "The hearing diary of a matter, with the form that records a hearing and fixes the next date.", 5.9),
    ("g_drafts_tab", "g_drafts_tab.png", "The drafts of a matter and their approval state.", 5.9),
    ("g_settle", "g_settle.png", "Settlement: the compounding cost at each stage, and instalments recorded.", 5.9),
    ("g_activity", "g_activity.png", "The append-only activity log of a matter.", 5.9),
    ("g_diary", "g_diary.png", "Diary: hearings and statutory deadlines on one month.", 5.9),
    ("g_drafts", "g_drafts.png", "Drafts: a legal notice built only from the matter's facts, waiting for an advocate's name.", 5.9),
    ("g_import", "g_import.png", "Recover: importing a bank's return file.", 5.9),
    ("g_phones", "g_phones.png", "At phone width: the home page, the menu, and a matter.", 5.9),
]

AZURE = [
    ("az_students", "az_students.png", "The Azure for Students subscription of the university account, with its credit.", 5.6),
    ("az_project", "az_project.png", "The Foundry project tarikh in the Azure for Students subscription.", 5.6),
    ("az_block", "az_quota_block.png", "A gpt-4.1 deployment refused for insufficient quota in Korea Central.", 4.4),
    ("az_quota", "az_quota.png", "Quota for the subscription in Korea Central: 0 tokens per minute for the base chat models.", 5.6),
    ("az_ftq", "az_ft_quota.png", "Quota that is available: fine-tuned gpt-4.1-mini and gpt-4.1-nano, 500,000 tokens per minute.", 5.6),
]


def appendices() -> list[tuple]:
    A: list[tuple] = []
    A.append(("h1a", "A", "AI-901 Course Syllabus"))
    A.append(("p", "Skills measured as of 15 April 2026, from Microsoft's study guide {c:exam}. The right-hand column shows where Tarikh uses the area."))
    A.append(("table", "syl", "AI-901 skills measured and their use in Tarikh",
              ["Domain and skill area", "Used in Tarikh"],
              [["**1. Identify AI concepts and capabilities (40-45%)**", ""],
               ["Describe principles of responsible AI", "Section 5.4"],
               ["Identify AI model components and configurations", "Model deployment and the weekly record, weeks 3-4"],
               ["Identify AI workloads: generative and agentic AI, text analysis, speech, vision, information extraction", "Each is used once in the pipeline (Table 3.2)"],
               ["**2. Implement AI solutions by using Microsoft Foundry (55-60%)**", ""],
               ["Implement generative AI apps and agents by using Foundry", "Brief drafting; the two-tool agent"],
               ["Implement AI solutions for text and speech", "PII masking; voice note and read-aloud"],
               ["Implement AI solutions with computer vision and image generation", "Cheque image observations"],
               ["Implement AI solutions for information extraction", "Model reader with a strict schema; Content Understanding analyzers for three papers"]],
              [4.0, 1.9]))
    A.append(("h1a", "B", "Course Certificate"))
    cert = HERE.parent / "assets" / "course_certificate.png"
    A.append(("certificate", str(cert) if cert.exists() else None))
    if cert.exists():
        A.append(("p", "Authenticated digital transcript from Certiport, issued 21 November 2026: Microsoft Certified Fundamentals, Microsoft Azure AI Fundamentals. "
                       "Exam AI-901, Microsoft Azure AI Fundamentals, passed on 28 October 2026, administered by Chandigarh University, in English."))
    A.append(("h1a", "C", "Screens of the Working Platform"))
    A.append(("p", "Each screen below was captured on 21 November 2026 from the running Tarikh server, signed in as a fictional advocate with the fictional sample matters loaded. "
                   "Every word on these screens is produced by the platform's own code; screens whose content would come from an Azure model are described in Chapter 4 instead."))
    for key, fname, cap, w in GALLERY:
        A.append(("fig", key, fname, cap, w))
    A.append(("h1a", "D", "Azure Deployment Record"))
    A.append(("p", "Screens from the student's Azure for Students subscription and the Foundry project `tarikh`, taken while the project was being set up. "
                   "They are reproduced in greyscale; the page addresses are cropped."))
    for key, fname, cap, w in AZURE:
        A.append(("fig", key, fname, cap, w))
    A.append(("h1a", "E", "Running the Project"))
    A.append(("p", "The commands below were used to set up and run the project. Full steps, with the Azure portal screens, are in `docs/azure-setup.md`."))
    A.append(("code", "az login\n"
                      "pip install -r requirements.txt\n"
                      "python -m tools.make_finetune      # writes data/finetune/train.jsonl and validation.jsonl\n"
                      "# Foundry portal: Training > Start training > gpt-4.1-mini, Supervised, Global;\n"
                      "#   upload both files; deploy the result as tarikh-reader on the Developer tier\n"
                      "python -m tools.check_setup        # one real call to each service, with a plain pass or fail\n"
                      "python -m tools.evaluate_reader    # field accuracy on the 9 validation papers\n"
                      "python -m uvicorn app.main:build_app --factory --port 8000\n"
                      "pytest                              # server and desk checks\n"
                      "cd site && python build.py && python -m pytest tests && node --test tests/engine.test.js\n"))
    A.append(("p", "The settings live in a `.env` file on the laptop, which is never committed: `TARIKH_MODE=live`, `AZURE_AI_PROJECT_ENDPOINT` (the project's endpoint), "
                   "`AZURE_AI_MODEL_DEPLOYMENT_NAME=tarikh-reader` and `TARIKH_EXTRACTOR=model`. No key is stored anywhere; `az login` and the two roles are enough."))
    A.append(("p", "Project layout: `app/` holds the server, accounts, pipeline and deadline engine; `app/services/` holds one file per Azure service; `site/` holds the website and the desk; "
                   "`tests/` holds the automated checks; `tools/` holds the setup helpers; `docs/` holds the engineering record; `report/` holds the script that built this document."))
    return A
