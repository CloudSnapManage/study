# Cognito Launch and Monetization Design

## Intent
Make Cognito commercially launchable as an offline-first paid desktop study product without turning core study data into a cloud dependency. The product has two tiers: Cognito Free and Cognito Pro.

## Product audit
The core application is differentiated by local PDF provenance, exam weighting, exact-page verification, spaced repetition, Obsidian-safe writes, and deterministic offline fallbacks. Launch gaps are entitlement enforcement, license activation/status UI, clear plan boundaries, persisted settings, PDF/diagram controls, and packaging/payment handoff documentation.

## Approaches considered
1. **Client-only `localStorage` Pro flag.** Rejected: trivial to modify and not enforceable at API boundaries.
2. **Mandatory account and hosted billing API.** Strong control but violates local-first operation and creates a server dependency before product-market validation.
3. **Signed offline licenses with provider-neutral checkout (selected).** A commerce provider or small fulfillment service signs short JSON licenses with an Ed25519 private key. Cognito embeds only the public key, verifies locally, persists the token, and enforces entitlements in backend routes. Checkout is an external configurable URL. This is launchable with any merchant-of-record and keeps private study data local.

## Tier boundaries
### Cognito Free
- Unlimited local PDF scanning and full-text search.
- Daily Sprint with SM-2 scheduling.
- Exam Radar and formula/diagram browsing.
- Local retrieval chat with citations and PDF verifier.
- One active model profile and graphite/paper themes.

### Cognito Pro
- Obsidian sync and thread export.
- Timed mock exams, grading, and missed-concept export.
- Solution Checker audits and error flashcards.
- OpenAI-compatible/custom model profiles and agent tool traces.
- Formula-to-Sprint actions and future export formats.
- Commercial license status, expiry, and offline grace display.

Free keeps the central local study promise. Pro gates workflows with recurring model/provider value or high-value synthesis, rather than artificially limiting file counts.

## License format and trust
A license token is `base64url(payload).base64url(signature)`. Payload fields are `license_id`, `tier`, `issued_at`, `expires_at`, `customer`, and optional `features`. The backend verifies the Ed25519 signature using `COGNITO_LICENSE_PUBLIC_KEY`, validates dates, and derives entitlements. The token is stored in SQLite settings; raw customer data never goes to the frontend except a masked identifier. An expired subscription receives a seven-day offline grace period; after grace, Pro routes return structured `402` JSON with code `pro_required`. No private signing key ships in Cognito.

## Checkout and activation
`COGNITO_CHECKOUT_URL` points to the selected provider checkout. The Plan drawer shows Free/Pro comparison, opens that URL in the system browser only after a user click, and accepts a signed license token. A future webhook/fulfillment service can email tokens or expose a copy action. The repository includes the license contract and a development signing utility that requires an external private key path; it never generates or stores a production key automatically.

## UI
Plan status belongs in utilitarian desktop chrome, not a marketing page:

```text
Settings
├─ Runtime
├─ Model
├─ Appearance
└─ Plan
   Free     Local study core
   Pro      Advanced workflows, custom providers, Obsidian
   [View Pro] [Activate license]
```

Locked actions stay visible with a small `PRO` badge and a precise explanation. The upgrade panel uses the existing graphite panes, hairline borders, tabular plan metadata, and amber only for the active CTA. No price is hard-coded because tax/currency belong to the checkout provider.

## Enforcement
Backend dependencies guard Pro routes. The frontend consumes `/api/license/status`, labels locked actions, and handles `402 pro_required` centrally. UI gating is explanatory; backend gating is authoritative.

## Launch readiness
Document checkout configuration, public-key setup, signing/fulfillment contract, and tier matrix. Add tests for valid, malformed, expired, grace-period, and tampered licenses plus all Pro route guards. A packaged executable and payment webhook remain deployment steps, not prerequisites for the local application architecture.
