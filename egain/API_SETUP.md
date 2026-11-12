# eGain Knowledge Hub API setup

SOLACE retrieves approved knowledge chunks from eGain AI Knowledge Hub using OAuth 2.0 client credentials and the documented AI Services Retrieve API. Obtain tenant-specific endpoints from eGain Client Application metadata.

## Environment variables

- `EGAIN_TOKEN_URL`: token endpoint from eGain metadata.
- `EGAIN_API_DOMAIN`: API domain from metadata.
- `EGAIN_CLIENT_ID` and `EGAIN_CLIENT_SECRET`: server-side credentials.
- `EGAIN_PORTAL_ID`: knowledge portal identifier.
- `EGAIN_SCOPE`: space-separated scopes assigned to the app (typically `app.knowledge.portalmgr.read app.core.aiservices.read`).
- `EGAIN_LANGUAGE`: language code, defaults to `en-US`.
- `SOLACE_API_KEY`: shared key required by SOLACE's server-side retrieval route.

Never expose credentials in browser JavaScript, commit them, or paste them into chat.

## Setup

1. In eGain Administration Console, create a Client Application in the relevant Partition.
2. Grant only the knowledge retrieval scopes required by the API.
3. Copy the Token URL and API Domain from that application's Metadata panel.
4. Confirm the portal ID, published content permissions and language.
5. Store the settings in the server's environment/secret manager.
6. Test with a non-sensitive query and verify returned source metadata.

## SOLACE retrieval endpoint

`POST /api/knowledge/retrieve`

Headers: `Content-Type: application/json`, `X-API-Key: <SOLACE_API_KEY>`

Body:
```json
{"query":"How do I report a lost document?","language":"en-US"}
```

The endpoint returns eGain retrieval results only. It requires the SOLACE API key and fails closed if the eGain tenant configuration is missing. It does not invent or generate an answer. The caller must ground any customer-facing response in the returned approved sources and abstain/escalate when evidence is missing, stale, contradictory or irrelevant.

`GET /egain/health` reports whether retrieval configuration is present; it does not validate live credentials.

## Official documentation

- [eGain API quickstart](https://apidev.egain.com/developer-portal/get-started/quickstart)
- [eGain API authentication guide](https://apidev.egain.com/developer-portal/get-started/authentication_guide)
- [eGain client credentials flow](https://apidev.egain.com/developer-portal/guides/authentication/client-credentials-flow)
