# SDK notes (read from the installed packages and Microsoft Learn on 2026-11-20)

Installed: azure-ai-projects 2.11.0, azure-ai-contentunderstanding 1.1.0, azure-ai-textanalytics 5.4.0, azure-identity 1.27.0, openai.

## One setting is enough
`AZURE_AI_PROJECT_ENDPOINT = https://<resource>.services.ai.azure.com/api/projects/<project>`.
Resource name is parsed from it, giving two base URLs for the same resource:
- `https://<resource>.services.ai.azure.com`      Foundry project, Content Understanding
- `https://<resource>.cognitiveservices.azure.com` Language, Speech REST (custom-domain endpoints; Entra bearer tokens work here)

## Content Understanding (azure-ai-contentunderstanding)
- `ContentUnderstandingClient(endpoint, credential)`; analysis is a long-running call:
  `client.begin_analyze_binary(analyzer_id, binary_input=bytes, content_type=...).result()` -> `AnalysisResult`.
- Custom analyzer: `client.begin_create_analyzer(analyzer_id, resource=<dict>, allow_replace=True).result()`.
  Verified REST shape: `baseAnalyzerId: "prebuilt-document"`, `config.estimateFieldSourceAndConfidence: true`,
  `fieldSchema.fields.<key>.{type, method:"extract", description, estimateSourceAndConfidence}`, `models.completion: "gpt-4.1"`.
- Needs model deployments gpt-4.1 (custom/prebuilt field analyzers), gpt-4.1-mini, text-embedding-3-large, mapped once with
  `client.update_defaults(...)`; the signed-in user needs role **Cognitive Services User** on the resource.
- Result: `result.contents[0].fields[key]` -> `ContentField` with `.value`, `.confidence`, `.source` (string, `D(page,x1,y1,...)`),
  plus `pages[i].width/height/unit` used to normalise polygons to 0..1.

## Language (azure-ai-textanalytics)
- `TextAnalyticsClient(endpoint, credential)`; `recognize_pii_entities`, `recognize_entities`, `extract_key_phrases`.
- Text PII language list includes Hindi (`hi`) and Punjabi (`pa`) (Microsoft Learn PII language support), so redaction runs in the
  source language; no translate-first route is needed.

## Speech (REST, no native SDK, so it installs anywhere)
- Fast transcription: `POST https://<resource>.cognitiveservices.azure.com/speechtotext/transcriptions:transcribe?api-version=2025-10-15`,
  multipart `audio` + `definition` JSON `{"locales":["hi-IN"]}`; header `Authorization: Bearer <Entra token>` (role Cognitive Services User).
  One locale = used directly; several = language identification (known to mis-script mixed Hindi/English), so we send one locale.
- Locale support is read at run time with `GET .../speechtotext/transcriptions/locales?api-version=2024-11-15`; the UI only offers
  en-IN / hi-IN / pa-IN if the service lists them. Punjabi fast-transcription support is not stated in the docs, so it is checked live.
- Text to speech: `POST https://<resource>.cognitiveservices.azure.com/tts/cognitiveservices/v1` with SSML, voice picked from the
  voices list for the locale.

## Foundry model and agent (azure-ai-projects 2.x)
- `AIProjectClient(endpoint, credential=DefaultAzureCredential())`; `project.get_openai_client()` returns an OpenAI-style client.
- Chat/brief/vision/translation: `openai.responses.create(model=<deployment>, input=[...])`.
- Agent: `project.agents.create_version(agent_name=..., definition=PromptAgentDefinition(model, instructions, tools=[FunctionTool(...)]))`;
  conversation via `openai.conversations.create()`; call
  `openai.responses.create(conversation=..., input=..., extra_body={"agent_reference": {"name": ..., "type": "agent_reference"}})`;
  for each `function_call` item run the tool locally and send back a `function_call_output` item with the same `call_id`.
- Entra ID is the supported authentication; `az login` is enough on a laptop.
