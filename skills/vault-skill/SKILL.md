---
name: vault-skill
description: "Hardware-anchored encrypted key vault and access memory skill. Provides JIT (Just-In-Time) secret injection, scope enforcement, and secret purpose catalogs without leaking raw credentials into chat or logs."
---

# 🛡️ Key Vault & Memory Access Skill

The **vault-skill** enables AI agents to securely interact with external APIs, production services, and credentials without storing plain-text keys in `.env`, chat transcripts, or configuration files.

---

## 🔒 Security Principles

1. **Hardware & Machine Binding**:
   - The encrypted vault (`vault.enc`) is anchored to this specific Windows PC via **Windows DPAPI** (`CryptProtectData`) combined with **AES-256-GCM**.
   - If copied to another machine, the vault **cannot be decrypted**, even if the attacker possesses the PIN.
2. **Zero-Leak Policy**:
   - Never output or echo decrypted secret values directly in chat responses, user-facing summaries, or logs.
   - Decrypted secrets must only be piped into runtime environment variables or memory JIT (Just-In-Time) operations.
3. **Semantic Memory Catalog**:
   - Before executing sensitive operations, inspect `catalog.json` or run `describe <KEY>` to verify permitted actions, environments, and policies.

---

## 🛠️ CLI Usage & Quick Reference

Script location:
```
python C:\Users\Dmytro\.gemini\config\skills\vault-skill\vault_manager.py <command>
```

### 1. View Available Secrets & Permissions
Does not require a PIN or decryption. Safe for agents to inspect anytime:
```bash
python vault_manager.py list
python vault_manager.py describe CLOUDFLARE_API_KEY
```

### 2. First-Time Setup: Set Master PIN
```bash
python vault_manager.py set-pin
# Prompts securely for PIN via getpass (no echo, no process args)
```

### 3. Store a Secret (Value Never Touches Process Args)
```powershell
# Best: value via environment variable (invisible to process listing)
$env:VAULT_PIN="YOUR_PIN"
$env:VAULT_SECRET_VALUE="v1.0_secret_here"
python vault_manager.py set CLOUDFLARE_API_KEY --desc "Cloudflare deployment token" --scope "staging,prod-deploy"

# Or: value via stdin pipe
echo "v1.0_secret_here" | python vault_manager.py set CLOUDFLARE_API_KEY --desc "..." --pin "YOUR_PIN"

# Legacy (value visible in process list — avoid on shared machines):
python vault_manager.py set CLOUDFLARE_API_KEY "v1.0_secret_here" --pin "YOUR_PIN"
```

### 4. JIT (Just-In-Time) Secret Retrieval
```powershell
# PIN via env var — never in process args
$env:VAULT_PIN="YOUR_PIN"
$env:CF_TOKEN = python vault_manager.py get CLOUDFLARE_API_KEY
npx wrangler deploy
```

### 5. Rotate Master PIN
Re-encrypts the entire vault with a new key. Old PIN required:
```bash
python vault_manager.py rotate-pin
# Prompts for old PIN, then new PIN
```

### 6. Delete a Secret
```bash
python vault_manager.py delete SOME_OLD_KEY
```

---

## 📋 Security Architecture Roadmap
See [`ROADMAP.md`](file:///C:/Users/Dmytro/.gemini/config/skills/vault-skill/ROADMAP.md) for upgrading to Face ID / WebAuthn, Passkeys, and TPM 2.0 direct hardware sealing.
