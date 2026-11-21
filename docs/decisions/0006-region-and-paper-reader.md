# 0006. Region choice and a second way to read papers

Status: accepted, 21 November 2026 (supersedes the open question in 0003)

## Context
The owner's Azure for Students subscription offered South India. Content Understanding is not offered in South India;
Microsoft lists it in regions such as East US 2, West US, Sweden Central and Australia East.

## Decision
1. Recommend **Sweden Central** (or East US 2): Content Understanding, the models, Speech, Language and the Agent Service
   are all available there, so every AI-901 capability runs as designed.
2. Keep a second reader, `ModelExtractor`, switched on with `TARIKH_EXTRACTOR=model`. The deployed vision model reads the
   paper into the same fields through a strict JSON schema. It returns no location boxes, so every value it reads is
   flagged "Read by the model without a location box. Check it against the paper."

## Costs if wrong
In model mode the paper view cannot draw boxes and confidence scores are absent. The facts, deadlines, drafts and audit
work the same. Changing region later needs only a new `.env`.
