# 🛡️ Vault Security Roadmap: Hardware Sealing, Remote Authorization & Passkeys

This roadmap outlines the evolution of the **Vault Skill** from a local DPAPI-protected store to an enterprise-grade, hardware-isolated zero-trust enclave with biometric remote verification.

---

## 📍 Phase 1: Local Hardware Anchoring (Current Baseline)
- [x] **Windows DPAPI Integration**: Symmetric keys encrypted and anchored to the local Windows machine profile and user SID via `CryptProtectData`.
- [x] **AES-256-GCM Payload Protection**: Authenticated encryption for all stored credentials with authenticated integrity check tags.
- [x] **Salted Argon2/PBKDF2 Hardware Verifier**: Master PIN verifier stored under a DPAPI hardware-sealed envelope.
- [x] **Safe Semantic Catalog**: Public metadata catalog (`catalog.json`) allowing AI agents to understand secret purposes and action limits without decryption.

---

## 📍 Phase 2: Remote PIN & Session Authorization (Mobile Readiness)
- [ ] **Ephemeral Session Tokens (Time-based Lease)**:
  - When the user controls the agent remotely via phone, prompt for Master PIN once per session.
  - Store an in-memory ephemeral lease token valid for `N` minutes (e.g., 30 minutes) using Windows Named Pipes or localhost Unix socket.
  - Automatic memory wipe upon inactivity or explicit `/lock` command.
- [ ] **Command Sandboxing**:
  - Restrict which commands can ingest secrets via an explicit whitelist (e.g., `wrangler deploy`, `git push`, `docker login`).
- [ ] **Brute-Force Rate Limiting**:
  - Add exponential backoff after N consecutive failed PIN attempts (e.g., 3 failures → 5s delay, 5 failures → 30s, 10 failures → lockout for 5 minutes).
  - Critical for the network-exposed daemon — a local CLI has DPAPI as its gate, but a daemon accepting remote unlock requests needs its own throttle.

---

## 📍 Phase 3: Biometric WebAuthn / Passkeys (Face ID & Touch ID from Mobile)
- [ ] **WebAuthn FIDO2 Challenge-Response Flow**:
  - Host a lightweight localhost authorization daemon on the PC (e.g., Python FastAPI / aiohttp).
  - When an agent requests a high-privilege secret (e.g. `PRODUCTION_DB_PASSWORD`), the daemon sends a push notification or Telegram prompt with a 1-click verification link.
  - Opening the link on the phone prompts for native **Face ID** / **Touch ID** via WebAuthn/Passkey.
  - The phone signs a cryptographic challenge with its Secure Enclave (Apple Secure Enclave / Android KeyStore) and transmits the proof back to the PC daemon.
  - The PC daemon validates the signature and releases the requested secret into the agent's execution context for a single run.

---

## 📍 Phase 4: TPM 2.0 PCR Sealing & Enclave Protection
- [ ] **Direct TPM 2.0 PCR Sealing**:
  - Migrate from DPAPI to Windows CNG (Cryptography Next Generation) with `MS_PLATFORM_CRYPTO_PROVIDER`.
  - Seal the master decryption key directly to TPM 2.0 Platform Configuration Registers (PCRs: Secure Boot enabled, BitLocker integrity intact).
  - If the OS is tampered with, booted into a live USB, or modified by malware, the TPM hardware chip physically refuses to unseal the vault.
- [ ] **Hardware Security Keys (YubiKey / Nitrokey)**:
  - Add optional FIDO2 / PIV smart card support requiring a physical touch on a USB hardware key before releasing critical master credentials.
