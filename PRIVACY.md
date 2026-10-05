# Privacy Policy for OmniArch

**Last Updated:** October 4, 2026

OmniArch ("we", "our", or "the App") is committed to protecting your privacy and ensuring you have a secure experience when generating architecture diagrams and scaffolding code from software repositories.

---

### 1. Data Collection and Usage

OmniArch operates on a **zero-retention, Bring-Your-Own-Key (BYOK)** principle:

1. **Source Code & AST Signatures:**
   - When you analyze a codebase (via GitHub URL, local directory, or specification text), OmniArch parses architectural signatures (routes, data models, message queues) in-memory solely for diagram synthesis.
   - **We do not store, log, or persist your source code, repository files, or AST data on our servers.** All processing is transient and purged immediately upon request completion.

2. **Secrets & Sensitive Data Redaction:**
   - OmniArch automatically scrubs private keys, API keys, passwords, database URIs, and bearer tokens from memory before dispatching any context to language models.

3. **Inference Credentials (BYOK):**
   - Your API keys (e.g., ModelScope, OpenAI, DeepSeek, OpenRouter, Groq) and Miro Access Tokens are stored strictly in your local browser's `localStorage` or injected via your secure CI environment.
   - Server-side sessions do not persist user AI API keys.

4. **Miro OAuth2 Tokens:**
   - If you install OmniArch via Miro OAuth2 authorization, workspace installation tokens are encrypted and retained only to facilitate board synchronization authorized by your team.

---

### 2. Third-Party Services and AI Providers

When you trigger an architecture synthesis, architectural metadata is dispatched exclusively to your selected AI provider (ModelScope Cloud, OpenAI, DeepSeek, Groq, OpenRouter, or local Ollama). Each provider processes requests according to their respective privacy standards and API data usage policies (e.g., standard API terms prohibiting training on customer API payloads).

---

### 3. Data Subject Rights (GDPR & CCPA Compliance)

Under GDPR and CCPA, you retain full rights to:
- Request deletion of any OAuth installation record associated with your Miro team ID (`DELETE /api/oauth/installations/{team_id}`).
- Revoke OmniArch access at any time directly through your [Miro Account Settings](https://miro.com/app/settings/).
- Inspect the open-source code repository to audit data flows and zero-retention policies.

---

### 4. Security & Communications

- All communication between client browsers, Miro Web SDK, and backend API endpoints is strictly enforced over TLS / HTTPS.
- Rate limiting and intrusion prevention mechanisms protect against abuse and unauthorized data access.

---

### 5. Contact & Support

If you have questions, inquiries, or security audit requests, please contact:
- **Repository:** [https://github.com/rpavani1998/omniarch](https://github.com/rpavani1998/omniarch)
- **Email:** support@omniarch.dev
