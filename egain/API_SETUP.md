# eGain Knowledge Hub API setup

SOLACE can retrieve approved knowledge chunks directly from eGain's AI Knowledge Hub. This implementation uses eGain's documented OAuth 2.0 client-credentials flow and the AI Services Retrieve API. It does not hard-code a tenant URL: obtain the Authorization URL, Token URL and API domain from the eGain Client Application metadata for your tenant.

## Environment variables

Copy `.env.example` into your deployment secret manager and fill in values from eGain:

- `EGAIN_TOKEN_URL`: token endpoint shown in Client Application metadata.
- `EGAIN_API_DOMAIN`: API domain shown in metadata.
- `EGAIN_CLIENT_ID` and `EGAIN_CLIENT_SECRET`: server-side credentials.
- `EGAIN_PORTAL_ID`: portal identifier, e.g. `PZ-...`.
- `EGAIN_SCOPE`: required space-separated application scopes assigned to the client application.
- `EGAIN_LANGUAGE`: language code, default `en-US`.

Never expose credentials in browser JavaScript, commit them, or paste them into chat.

## eGain console steps

1. In the eGain Administration Console, open the relevant Partition and create a Client Application under Integration.
2. Grant only the required knowledge retrieval scopes (the eGain developer quickstart documents `app.knowledge.portalmgr.read` and `app.core.aiservices.read` for Answers/Retrieve/Search use).
3. Use the Client Application metadata to copy the tenant-specific token URL and API domain.
4. Obtain the portal ID and ensure the app can read the intended published knowledge portal and language.
5. Add the settings above to the server's secret manager.
6. Run the retrieval tests, then make a live request using a non-sensitive test question.
7. Verify that each returned chunk includes traceable source metadata before using it to ground a customer-facing response.

## Retrieval-first response policy

The client calls:

`POST {EGAIN_API_DOMAIN}/core/aiservices/v4/{EGAIN_PORTAL_ID}/retrieve?q=...&$lang=...`

with an OAuth bearer token. It returns retrieved source material only; it does not turn retrieved text into legal, financial or government advice. The application layer must cite the returned sources, apply the approved response policy, and abstain/escalate if retrieval is empty, stale, contradictory or irrelevant.

The exact token URL and API domain vary by tenant. Do not infer them from examples.

## Official documentation

- [eGain API quickstart](https://apidev.egain.com/developer-portal/get-started/quickstart)
- [eGain API authentication overview](https://apidev.egain.com/developer-portal/api-overview)
- [eGain Knowledge Hub Portal Manager API](https://apidev.egain.com/developer-portal/guides/knowledge/knowledge)
