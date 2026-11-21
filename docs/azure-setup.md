# Azure setup for Tarikh (Azure for Students, Korea Central)

This is the path the project actually took. Each step says what you have at the end. Nothing in this project stores a
key: the app signs in as you through `az login`, and the settings live in a `.env` file on your laptop that is never
committed.

What exists already (21 November 2026):

| Thing | Name |
|---|---|
| Subscription | Azure for Students (24BAI70769@cuchd.in), US$100 credit, expires 20 Nov 2027 |
| Region | Korea Central (the policy allows only Central India, East Asia, Indonesia Central, Korea Central, UAE North) |
| Resource group | `tarikh-rg` |
| Foundry resource | `tarikh-24bai70769` |
| Foundry project | `tarikh` |
| Model deployment | `tarikh-reader` (fine-tuned gpt-4.1-mini, Developer tier) |

Why fine-tuning: in Korea Central this subscription has **0 tokens per minute** for every base chat model (the portal
refuses gpt-4.1 with "insufficient quota"), but **500,000 tokens per minute** for fine-tuned gpt-4.1-mini on the
Developer tier. A Developer deployment costs nothing while idle (pay per token, no hourly fee) and lasts 24 hours.

## 1. Fine-tune the reader (Foundry portal, about 5 minutes of clicks, then waiting)

1. Foundry portal, project **tarikh**, left menu **Training**, **Start training**. (Not "Clone training": that is
   Microsoft's Python-code example.)
2. **Basic details:** Customization method **Supervised**; Model **gpt-4.1-mini**; Training type **Global**. **Next**.
3. **Datasets:** Training data, **Upload**, `data/finetune/train.jsonl`. Validation data, **Upload**,
   `data/finetune/validation.jsonl`. **Next**. (Regenerate both with `python -m tools.make_finetune` if needed.)
4. **Optional settings:** Display name `tarikh-reader`. Leave batch size, epochs and learning rate on Default. **Submit**.
5. Wait until the job says **Succeeded** (often 30 to 90 minutes).
6. Open the finished job, **Deploy**. Deployment name **`tarikh-reader`**. Deployment type **Developer**
   (not Global Standard, which charges by the hour). **Deploy**.

**Done when:** Models, Deployments lists `tarikh-reader` as Succeeded. Renew it on any day you use the desk.

## 2. Give your own sign-in the roles it needs

Azure portal, **Resource groups, tarikh-rg, tarikh-24bai70769, Access control (IAM), Add, Add role assignment**.
Add both to your own account:

- **Cognitive Services User**
- **Foundry User** (previously called **Azure AI User**)

Wait two minutes. **Done when:** both show under Role assignments.

## 3. The laptop (Windows, PowerShell)

```powershell
winget install -e --id Microsoft.AzureCLI      # once; then open a NEW PowerShell window
az login                                       # sign in with 24BAI70769@cuchd.in
az account set --subscription "Azure for Students"

cd tarikh
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
notepad .env
```

In `.env` set (the endpoint is on the project's **Home** page in Foundry, "Project endpoint"; it is not a secret):

```
TARIKH_MODE=live
AZURE_AI_PROJECT_ENDPOINT=https://tarikh-24bai70769.services.ai.azure.com/api/projects/tarikh
AZURE_AI_MODEL_DEPLOYMENT_NAME=tarikh-reader
TARIKH_EXTRACTOR=model
```

Use the endpoint exactly as the Home page shows it.

## 4. Check, measure, run

```powershell
python -m tools.check_setup        # one real call per service; PASS or FAIL with the fix in plain words
python -m tools.evaluate_reader    # field accuracy on the 9 validation papers
python -m uvicorn app.main:build_app --factory --port 8000
```

Open <http://localhost:8000>, **Start free**, create your account, **Load sample matters**.

## Costs and cleanup

Training and use are billed per token from the US$100 credit; the Developer deployment has no hourly fee. After the
viva, delete everything with `az group delete --name tarikh-rg`.

## Sources checked

- Fine-tuning deployment types and charges: <https://learn.microsoft.com/azure/foundry/openai/how-to/fine-tuning-cost-management>
- Developer tier deployment (24 hours, no hosting fee): <https://learn.microsoft.com/azure/ai-services/openai/how-to/fine-tune-test>
- Agent Service regions: <https://learn.microsoft.com/azure/foundry/agents/concepts/limits-quotas-regions>
- Speech regions: <https://learn.microsoft.com/azure/ai-services/speech-service/regions>
- Content Understanding regions: <https://learn.microsoft.com/azure/ai-services/content-understanding/language-region-support>
