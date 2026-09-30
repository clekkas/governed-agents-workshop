# Healthcare Content Safety — guidance for Kaiser Permanente

> Addresses Sarita's concern: the generic content filter flags benign clinical language (e.g. "can I
> use Tylenol") and blocks legitimate healthcare responses. How to configure layered content safety
> so clinical use cases work without lowering the safety bar — and the path when the filter is wrong.
>
> Grounded in Microsoft Learn: **Azure AI Content Safety** (`/azure/ai-services/content-safety/`),
> **Foundry content filtering** (`/azure/ai-foundry/concepts/content-filtering`), and the layered
> guardrail model in `policy/guardrails.md`. Verify category/severity specifics at delivery time.

## Why medical false positives happen

Azure AI Content Safety models are **general-purpose**, not healthcare-tuned. They score four harm
categories (hate, sexual, violence, self-harm) by **severity**, plus optional **prompt shields**
(jailbreak), **protected material**, and **groundedness** detection. Clinical language —
medications, dosing, self-harm-adjacent screening, anatomy, violence in an injury history — can trip
the generic categories even when the intent is legitimate care. That's the "Tylenol gets flagged"
problem: a benign medication question scored against a generic filter.

## The fix is layered, not "turn the filter down"

Do not solve false positives by globally weakening the filter — that lowers safety for real threats.
Use **layers**, each tunable independently (matches the six-layer model in `policy/guardrails.md`):

| Layer | Where | What it does | Tuning for healthcare |
| --- | --- | --- | --- |
| **1. Input / request filter** | Before the model | Blocks obviously unsafe prompts + prompt-shield jailbreaks | Set **severity thresholds** per category; allow clinical-context terms |
| **2. App-side pre-filter** | Your code | Regex/allowlist for known clinical vocabulary; add context | Whitelist medication/vitals/screening terms so they aren't naively blocked |
| **3. Model content filter** | Azure OpenAI/Foundry deployment | Category+severity filtering on prompt and completion | Configure a **custom content filter** on the deployment; raise thresholds where clinically justified; request exceptions via the ticket path |
| **4. Groundedness / RAG** | Retrieval | Require cited evidence; refuse ungrounded claims | Keeps clinical answers tied to approved protocols, not model memory |
| **5. App-side post-filter** | Your code | Scan the response before it reaches the user | Catch prohibited claims (e.g. "safe to discharge") the generic filter won't |
| **6. Human approval** | HITL | Route uncertain/consequential outputs to a clinician | The final safety net for anything the filters can't adjudicate |

Key idea: **request filtering, response filtering, and app-side filtering are separate knobs.** A
false positive on a benign medication question is usually fixed at Layers 2–3 (context + threshold),
not by disabling safety.

## Configuring the model content filter

- In Foundry/Azure OpenAI, attach a **custom content filter** to the model deployment rather than
  relying on the default. Set per-category severity thresholds and enable prompt shields + protected
  material as policy requires.
- Where the platform supports it, use **allowlist/blocklist** and **custom categories** to encode
  KP-approved clinical terminology so it isn't caught by the generic categories.
- Test with a **healthcare false-positive suite** (benign clinical prompts that must pass) alongside
  the adversarial suite (unsafe prompts that must block). Both live next to
  `policy/guardrail-test-matrix.md` and `evaluation/adversarial-cases.jsonl`.

## When the filter is still wrong: the escalation path

Some clinical false positives need a platform-side adjustment. The working process (as used with
Pradip's team):
1. Reproduce the flagged prompt/response and capture the category + severity returned.
2. Apply the app-side + deployment-level mitigations above first.
3. If still incorrectly blocked, **open a ticket with the product team** for content-filter guidance
   or an exception; content-safety models get **monthly updates**, so track the fix across releases.
4. Record the case in the guardrail test matrix so a future model update can't regress it silently.

## What to tell app teams

- Content safety is **layered**; never fix a false positive by globally lowering severity.
- Encode **approved clinical vocabulary** at the app layer and in a **custom content filter** on the
  deployment; keep request/response/app filters as independent knobs.
- Keep a **false-positive test suite** next to the adversarial suite; both gate release.
- Use the **ticket path** for genuine model-filter errors, and re-verify after monthly model updates.

## Workshop mapping

- Extends `policy/guardrails.md` (six layers), `policy/guardrail-test-matrix.md`, and
  `policy/prohibited-claims.md`. Demo: show a benign clinical prompt passing after Layer-2/3 tuning,
  and a prohibited "safe to discharge" claim still blocked at Layer 5.

## References (public)

- Azure AI Content Safety: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/overview
- Foundry content filtering & custom filters: https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/content-filtering
- Prompt shields: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/jailbreak-detection
