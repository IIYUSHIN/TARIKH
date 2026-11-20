# Azure setup for Tarikh

Do these in order. Each step says what you will have at the end. Where Microsoft's own documentation did not give exact
button labels, the step says so; follow what you see on screen and send me a screenshot if it differs.

You will end with: one Azure account, one Foundry project in **Southeast Asia**, three deployed models, three roles on
your own sign-in, and a `.env` file. Nothing in this project stores a key. The app signs in as you, through `az login`.

## 1. Get an Azure account

Go to <https://azure.microsoft.com/free/students> and sign in with your **university email** (the one Chandigarh
University gave you). Azure for Students gives US$100 of credit for 12 months and needs no credit card. Microsoft checks
your student status against your email domain.

If it says it cannot confirm your university, that is a known problem for some Indian institutions and Microsoft's own
forum says a person cannot override it by hand. Then tell me the exact message. The fallback is the ordinary Azure free
account, which asks for a payment method to confirm who you are. Do not use it before you tell me, because I want to
confirm the cost of the three models first (each demo run costs a few rupees, not hundreds).

**Done when:** you can open <https://portal.azure.com> and see a subscription named "Azure for Students".

## 2. Install the Azure command-line tool and sign in

1. Install Azure CLI from <https://learn.microsoft.com/cli/azure/install-azure-cli> (Windows: the MSI installer).
2. Open a new terminal and run `az login`. A browser window opens. Sign in with the same account.
3. Run `az account show`. It prints your subscription. If it prints more than one, run
   `az account set --subscription "Azure for Students"`.

**Done when:** `az account show` shows the Azure for Students subscription.

## 3. Create the Foundry project (this also creates the resource)

Region matters. I checked Microsoft's pages for every service Tarikh uses. **Southeast Asia** supports all of them:
Foundry projects, Content Understanding, Speech fast transcription, neural text to speech, Foundry Agent Service, and
gpt-4.1 (Global Standard). It is also the nearest to you. Central India is **not** usable, because it lacks Content
Understanding and Agent Service.

1. Open <https://ai.azure.com> and sign in. Make sure the **New Foundry** toggle is on.
2. Click the project name at top left, then **Create new project**.
3. Type a name, for example `tarikh`. Open **Advanced options**.
4. Keep a new **Resource group** (give it a name you will remember, for example `rg-tarikh`). Set **Location** to
   **Southeast Asia**. Click **Create** and wait until it finishes.
5. On the project **Home** page copy the **Project endpoint**. It looks like
   `https://<resource>.services.ai.azure.com/api/projects/<project>`. You do not need the API key.

If Southeast Asia is missing from the list (student subscriptions sometimes limit regions), choose one of these, which I
verified for all of the same services: **Sweden Central, UK South, Australia East, Japan East, East US 2**. Tell me which.

**Done when:** you have the project endpoint copied into a note.

## 4. Deploy the three models

Content Understanding needs `gpt-4.1`, `gpt-4.1-mini` and `text-embedding-3-large`. Let the helper do it. You need two
names: the **resource name** (the first part of your endpoint, before `.services.ai.azure.com`) and the **resource
group** from step 3.

```
python -m tools.deploy_models --account <resource-name> --group rg-tarikh
```

It lists what your resource offers, picks the newest version of each model, deploys them as Global Standard with names
equal to the model names, and skips any that already exist. Deployment names are what `.env` uses.

If it prints a quota error, open the Foundry portal, find your project's models page (**Models + endpoints**, or
**Deployments**; Microsoft's current docs did not give me the exact label), choose **Deploy model**, search
`gpt-4.1`, pick **Global Standard**, name it `gpt-4.1`, and lower the capacity. Repeat for the other two.

**Done when:** the three names appear in the portal's deployments list with status Succeeded.

## 5. Give your own sign-in the roles it needs

Owning the subscription lets you create things but does not let your code call them. In the portal:
**Resource groups, rg-tarikh, the Foundry resource, Access control (IAM), Add, Add role assignment.** Add these two roles
to **yourself** (Members tab, Select members, search your own email):

- **Cognitive Services User** (needed by Content Understanding, Language and Speech)
- **Foundry User** (previously called **Azure AI User**; needed by agents and the model)

Wait two minutes after saving. Role changes are not instant.

**Done when:** both roles show for your email under Role assignments.

## 6. Install Tarikh's dependencies

```
python -m venv .venv
.venv\Scripts\activate          (Windows)   |   source .venv/bin/activate   (macOS, Linux)
pip install -r requirements.txt
```

## 7. Write `.env`

Copy `.env.example` to `.env` and fill in:

```
TARIKH_MODE=live
AZURE_AI_PROJECT_ENDPOINT=<the endpoint from step 3>
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4.1
```

If you named the other two deployments differently in step 4, also set `TARIKH_CU_MINI_DEPLOYMENT` and
`TARIKH_CU_EMBEDDING_DEPLOYMENT`.

## 8. Check everything with one command

```
python -m tools.check_setup
```

It makes one real call to each service, using the same code the app uses, and prints PASS or FAIL with what to fix in
plain words. It reads the sample cheque, masks a phone number, speaks a sentence, listens to it, and asks the agent a
question. Run it until every line says PASS. **Send me the output of the first run, pass or fail.**

Two results to note: the line for Speech listening prints which of English, Hindi and Punjabi your region offers. Punjabi
voice notes appear only if Azure Speech lists `pa-IN` for fast transcription; if it does not, the app says so on screen
and the report says so too. That is an honest limit, not a bug.

## 9. Run the app and record the evidence run

```
python -m uvicorn app.main:build_app --factory --port 8000
```

Open <http://localhost:8000>, choose **Open the fictional sample matter**. While you use it, the app saves every Azure
reply to `data/cassettes/`. Those files are the evidence for the report and the safety net for the viva: with
`TARIKH_MODE=replay` the app replays them with no internet and shows a banner saying so.

## Costs and cleanup

Models are billed per token. A full demo run costs a few rupees. When the exam is over, delete the resource group
(`az group delete --name rg-tarikh`) so nothing keeps billing; the credit and the free services do not need cleanup.

## Sources checked

- Azure for Students: <https://azure.microsoft.com/free/students> (US$100, 12 months, no card, school email)
- Create a Foundry project, roles: <https://learn.microsoft.com/azure/foundry/how-to/create-projects>
- Content Understanding regions: <https://learn.microsoft.com/azure/ai-services/content-understanding/language-region-support>
- Speech fast transcription regions: <https://learn.microsoft.com/azure/ai-services/speech-service/regions>
- Agent Service regions: <https://learn.microsoft.com/azure/foundry/agents/concepts/limits-quotas-regions>
- Model deployment by CLI: <https://learn.microsoft.com/azure/foundry/foundry-models/how-to/create-model-deployments>
