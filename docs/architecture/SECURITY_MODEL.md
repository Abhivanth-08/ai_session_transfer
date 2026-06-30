# MemoryBridge Security Model

## 1. Core Security Principles
- **Zero Trust Cloud**: The cloud backend should be treated as untrusted.
- **End-to-End Encryption (E2EE)**: In Mode 3 (Full Sync), source code is encrypted before leaving the user's device.
- **No Telemetry**: The local application and extensions never send unprompted telemetry to external servers.

## 2. Encryption Strategy
1. **Client-Side Key Generation**: When a user initializes MemoryBridge, an AES-256 master key is generated locally.
2. **Object Encryption**: All `base.tar.gz` and `.patch` files are encrypted via AES-256-GCM using the master key before being uploaded to S3.
3. **Key Management**: The master key is never sent to the FastAPI backend in plaintext. If the user wishes to sync across devices, they must manually input their master passphrase on the new device, or securely exchange it using a public key infrastructure (PKI) tied to their devices.

## 3. Local Security
- `.aisession` directories contain sensitive conversation histories (which may include API keys if the user accidentally pasted them). 
- `.aisession/local.db` file permissions are restricted to the local user (e.g., `chmod 600` equivalent on UNIX, ACLs on Windows).
- **Secrets Filtering**: The Workspace Analyzer includes an optional "Secret Redactor" module that uses regex and entropy scanning (similar to TruffleHog) to prevent API keys from being committed to the snapshot engine.

## 4. API Security
- **Authentication**: JWT-based authentication for all endpoints.
- **Rate Limiting**: Applied to `/api/v1/sessions/*/snapshots/presigned-url` to prevent cloud storage abuse.
- **Pre-signed URLs**: Upload/Download URLs are short-lived (e.g., expire in 15 minutes) and restricted to the specific object path.
