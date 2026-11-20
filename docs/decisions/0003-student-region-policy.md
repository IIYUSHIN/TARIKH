# 0003 The student subscription's allowed regions decide the architecture

**Status:** Blocked until Piyush sends the allowed-regions list from his subscription.

**Context:** The screenshot shows an Azure for Students subscription with $100 of credit, expiring 20 November 2027, for the
account 24BAI70769@cuchd.in. It does not show which regions the subscription may deploy to.
Microsoft enforces an "Allowed resource deployment regions" policy on Azure for Students, and the list differs between
subscriptions. Community reports show lists of five regions such as Austria East, Malaysia West, Norway East,
Switzerland North and Brazil South, with Foundry deployments failing for students whose regions did not host it.

Azure Content Understanding is available in these 12 regions: Australia East, Canada Central, East US, East US 2, Japan East,
South Central US, Southeast Asia, Sweden Central, UK South, West Europe, West US, West US 3
([Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/language-region-support)).

**Decision:** Do not create any Azure resource, and do not finalise the architecture, until the real allowed list is known.
Then take the first row that fits:

| Allowed regions | Then |
| --- | --- |
| Include at least one of the 12 Content Understanding regions, and Foundry models, Speech and Language are available there | Keep the v0 architecture, in that region |
| Include none of the 12 | Ask Microsoft for region access ([process](https://learn.microsoft.com/en-us/troubleshoot/azure/general/region-access-request-process)) |
| Region access is refused or too slow | Piyush decides: upgrade to pay-as-you-go (needs a card, and real spending), or replace Content Understanding with the multimodal model's structured output in an allowed Foundry region |

**Why:** A wrong region wastes a day of setup and ends in a policy error with no fix on our side. The check takes five minutes.

**Cost if wrong:** If the list is read wrongly, deployment fails with `RequestDisallowedByAzure` and nothing is billed.

**What Piyush does:** Portal, search "Policy", then Authoring, then Assignments, open "Allowed resource deployment regions"
(sometimes named "Allowed locations"), open the Parameters tab, and send a screenshot of the list.
