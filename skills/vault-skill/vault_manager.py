import os
import sys
import json
import base64
import hashlib
import hmac
import getpass
import ctypes
from ctypes import wintypes
from typing import Optional, Dict, Any

# --- Windows DPAPI Binding via ctypes ---
class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte))
    ]

CryptProtectData = ctypes.windll.crypt32.CryptProtectData
CryptProtectData.argtypes = [
    ctypes.POINTER(DATA_BLOB), # pDataIn
    wintypes.LPCWSTR,          # szDataDescr
    ctypes.POINTER(DATA_BLOB), # pOptionalEntropy
    ctypes.c_void_p,           # pvReserved
    ctypes.c_void_p,           # pPromptStruct
    wintypes.DWORD,            # dwFlags: CRYPTPROTECT_UI_FORBIDDEN = 0x1
    ctypes.POINTER(DATA_BLOB)  # pDataOut
]
CryptProtectData.restype = wintypes.BOOL

CryptUnprotectData = ctypes.windll.crypt32.CryptUnprotectData
CryptUnprotectData.argtypes = [
    ctypes.POINTER(DATA_BLOB), # pDataIn
    ctypes.c_void_p,           # ppszDataDescr
    ctypes.POINTER(DATA_BLOB), # pOptionalEntropy
    ctypes.c_void_p,           # pvReserved
    ctypes.c_void_p,           # pPromptStruct
    wintypes.DWORD,            # dwFlags
    ctypes.POINTER(DATA_BLOB)  # pDataOut
]
CryptUnprotectData.restype = wintypes.BOOL

LocalFree = ctypes.windll.kernel32.LocalFree
LocalFree.argtypes = [ctypes.c_void_p]
LocalFree.restype = ctypes.c_void_p

CRYPTPROTECT_UI_FORBIDDEN = 0x1

def _to_blob(data: bytes) -> DATA_BLOB:
    blob = DATA_BLOB()
    blob.cbData = len(data)
    blob.pbData = (ctypes.c_byte * len(data))(*data)
    return blob

def _from_blob(blob: DATA_BLOB) -> bytes:
    buffer = (ctypes.c_byte * blob.cbData).from_address(ctypes.addressof(blob.pbData.contents))
    data = bytes(buffer)
    LocalFree(blob.pbData)
    return data

def dpapi_encrypt(data: bytes, entropy: Optional[bytes] = None) -> bytes:
    """Hardware & machine-bound encryption using Windows DPAPI."""
    in_blob = _to_blob(data)
    out_blob = DATA_BLOB()
    entropy_blob = _to_blob(entropy) if entropy else None
    entropy_ptr = ctypes.byref(entropy_blob) if entropy_blob else None

    res = CryptProtectData(
        ctypes.byref(in_blob),
        "HardwareBoundVaultKey",
        entropy_ptr,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(out_blob)
    )
    if not res:
        raise OSError(f"DPAPI Encryption failed with error code: {ctypes.GetLastError()}")
    return _from_blob(out_blob)

def dpapi_decrypt(data: bytes, entropy: Optional[bytes] = None) -> bytes:
    """Hardware & machine-bound decryption using Windows DPAPI."""
    in_blob = _to_blob(data)
    out_blob = DATA_BLOB()
    entropy_blob = _to_blob(entropy) if entropy else None
    entropy_ptr = ctypes.byref(entropy_blob) if entropy_blob else None

    res = CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        entropy_ptr,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(out_blob)
    )
    if not res:
        raise OSError(f"DPAPI Decryption failed. Cannot decrypt on this machine/account. Code: {ctypes.GetLastError()}")
    return _from_blob(out_blob)

# --- AES-256-GCM Layer ---
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_DATA_PATH = os.path.join(SKILL_DIR, "vault.enc")
VAULT_TMP_PATH = os.path.join(SKILL_DIR, "vault.enc.tmp")
PIN_METADATA_PATH = os.path.join(SKILL_DIR, "auth_pin.json")
CATALOG_PATH = os.path.join(SKILL_DIR, "catalog.json")

PBKDF2_ITERATIONS = 120_000
FALLBACK_SALT = b"HARDWARE_STATIC_SEED_INIT_V1"

def _derive_key(pin: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from PIN + salt using PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8") if pin else b"DEFAULT_DEVICE_KEY",
        salt,
        PBKDF2_ITERATIONS,
    )

def _derive_pin_verifier(pin: str, salt: bytes) -> bytes:
    """Derive a verification hash for PIN comparison (PBKDF2-HMAC-SHA256)."""
    return hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, PBKDF2_ITERATIONS)


class VaultManager:
    def __init__(self):
        self._pin_meta_cache: Optional[Dict[str, str]] = None
        self._ensure_files()

    def _ensure_files(self):
        if not os.path.exists(CATALOG_PATH):
            with open(CATALOG_PATH, "w", encoding="utf-8") as f:
                json.dump({"secrets": {}}, f, indent=2)

    def _load_pin_meta(self) -> Optional[Dict[str, str]]:
        """Load and cache auth_pin.json to avoid redundant disk reads."""
        if self._pin_meta_cache is not None:
            return self._pin_meta_cache
        if not os.path.exists(PIN_METADATA_PATH):
            return None
        with open(PIN_METADATA_PATH, "r", encoding="utf-8") as f:
            self._pin_meta_cache = json.load(f)
        return self._pin_meta_cache

    def _invalidate_pin_cache(self):
        self._pin_meta_cache = None

    def is_pin_set(self) -> bool:
        return self._load_pin_meta() is not None

    def _get_encryption_salt(self) -> bytes:
        """Return the random salt stored with the PIN, or a static fallback if no PIN is configured."""
        meta = self._load_pin_meta()
        if meta:
            return base64.b64decode(meta["salt_b64"])
        return FALLBACK_SALT

    def set_pin(self, pin: str):
        """Initialize the Master PIN. Fails if a vault already exists (use rotate-pin instead)."""
        if len(pin) < 4:
            raise ValueError("PIN must be at least 4 characters/digits.")

        if os.path.exists(VAULT_DATA_PATH):
            raise RuntimeError(
                "A vault already exists. Use 'rotate-pin' to change the PIN "
                "so existing secrets are re-encrypted with the new key."
            )

        salt = os.urandom(16)
        derived = _derive_pin_verifier(pin, salt)
        dpapi_protected_hash = dpapi_encrypt(derived)

        meta = {
            "salt_b64": base64.b64encode(salt).decode("utf-8"),
            "verifier_dpapi_b64": base64.b64encode(dpapi_protected_hash).decode("utf-8"),
        }
        with open(PIN_METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        self._invalidate_pin_cache()
        print("[SUCCESS] Master PIN set and hardware-anchored with DPAPI.")

    def rotate_pin(self, old_pin: str, new_pin: str):
        """Change the Master PIN and re-encrypt the entire vault with the new derived key.

        Order of operations for crash safety:
        1. Decrypt vault with old PIN (validates old credentials)
        2. Encrypt vault with new key → vault.enc.tmp (old vault.enc untouched)
        3. Write new auth_pin.json (new verifier + new salt)
        4. os.replace vault.enc.tmp → vault.enc (atomic rename)
        If crash between 3 and 4: new PIN on disk, old vault — but the new PIN's
        salt can re-derive the new key, and vault.enc.tmp holds the valid data.
        """
        if len(new_pin) < 4:
            raise ValueError("New PIN must be at least 4 characters/digits.")

        # Step 1: decrypt with old credentials
        vault_data = self._load_vault(old_pin)

        # Step 2: prepare new PIN metadata (in memory, not written yet)
        new_salt = os.urandom(16)
        new_derived = _derive_pin_verifier(new_pin, new_salt)
        dpapi_protected_hash = dpapi_encrypt(new_derived)
        new_meta = {
            "salt_b64": base64.b64encode(new_salt).decode("utf-8"),
            "verifier_dpapi_b64": base64.b64encode(dpapi_protected_hash).decode("utf-8"),
        }

        # Step 3: encrypt vault with new key → tmp file (old vault.enc still intact)
        if vault_data:
            new_protected = self._encrypt_vault_bytes(vault_data, new_salt, new_pin)
            with open(VAULT_TMP_PATH, "wb") as f:
                f.write(new_protected)
                f.flush()
                os.fsync(f.fileno())

        # Step 4: write new PIN metadata
        with open(PIN_METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(new_meta, f, indent=2)
        self._invalidate_pin_cache()

        # Step 5: atomic rename vault (the only moment the old vault disappears)
        if vault_data:
            os.replace(VAULT_TMP_PATH, VAULT_DATA_PATH)

        print("[SUCCESS] Master PIN rotated and vault re-encrypted.")

    def verify_pin(self, pin: str) -> bool:
        meta = self._load_pin_meta()
        if meta is None:
            return True  # PIN not yet configured
        salt = base64.b64decode(meta["salt_b64"])
        stored_hash = dpapi_decrypt(base64.b64decode(meta["verifier_dpapi_b64"]))
        candidate_hash = _derive_pin_verifier(pin, salt)
        # Constant-time comparison to prevent timing side-channel attacks
        return hmac.compare_digest(candidate_hash, stored_hash)

    def _decrypt_vault_bytes(self, raw_data: bytes, salt: bytes, pin: str) -> Dict[str, Any]:
        """Decrypt raw vault bytes using DPAPI + AES-GCM with the given salt and PIN."""
        aes_container = dpapi_decrypt(raw_data)
        nonce = aes_container[:12]
        ciphertext = aes_container[12:]
        key = _derive_key(pin, salt)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(plaintext.decode("utf-8"))

    def _encrypt_vault_bytes(self, data: Dict[str, Any], salt: bytes, pin: str) -> bytes:
        """Encrypt vault data with AES-GCM + DPAPI using the given salt and PIN."""
        key = _derive_key(pin, salt)
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, json.dumps(data).encode("utf-8"), None)
        return dpapi_encrypt(nonce + ciphertext)

    def _atomic_write_vault(self, protected_bytes: bytes):
        """Write vault bytes atomically: tmp → fsync → rename."""
        with open(VAULT_TMP_PATH, "wb") as f:
            f.write(protected_bytes)
            f.flush()
            os.fsync(f.fileno())
        os.replace(VAULT_TMP_PATH, VAULT_DATA_PATH)

    def _load_vault(self, pin: str, _pin_already_verified: bool = False) -> Dict[str, Any]:
        if not os.path.exists(VAULT_DATA_PATH):
            return {}

        if not _pin_already_verified and self.is_pin_set() and not self.verify_pin(pin):
            raise PermissionError("Invalid Master PIN or hardware verification failed.")

        with open(VAULT_DATA_PATH, "rb") as f:
            raw_data = f.read()

        return self._decrypt_vault_bytes(raw_data, self._get_encryption_salt(), pin)

    def _save_vault(self, data: Dict[str, Any], pin: str, _pin_already_verified: bool = False):
        """Atomically write the vault: encrypt → write tmp → rename."""
        if not _pin_already_verified and self.is_pin_set() and not self.verify_pin(pin):
            raise PermissionError("Invalid Master PIN or hardware verification failed.")

        protected_bytes = self._encrypt_vault_bytes(data, self._get_encryption_salt(), pin)
        self._atomic_write_vault(protected_bytes)

    def set_secret(self, key_name: str, secret_val: str, description: str = "", scope: str = "general", pin: str = ""):
        if self.is_pin_set() and not self.verify_pin(pin):
            raise PermissionError("Invalid Master PIN or hardware verification failed.")
        vault = self._load_vault(pin, _pin_already_verified=True)
        vault[key_name] = secret_val
        self._save_vault(vault, pin, _pin_already_verified=True)

        # Update metadata catalog (no secrets stored here, safe for AI reflection)
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        catalog["secrets"][key_name] = {
            "description": description or f"Secret token for {key_name}",
            "scope": scope,
            "status": "configured",
        }
        with open(CATALOG_PATH, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2)
        print(f"[SUCCESS] Secret '{key_name}' securely encrypted and stored in vault.")

    def get_secret(self, key_name: str, pin: str = "") -> str:
        vault = self._load_vault(pin)
        if key_name not in vault:
            raise KeyError(f"Secret '{key_name}' not found in vault.")
        return vault[key_name]

    def delete_secret(self, key_name: str, pin: str = ""):
        if self.is_pin_set() and not self.verify_pin(pin):
            raise PermissionError("Invalid Master PIN or hardware verification failed.")
        vault = self._load_vault(pin, _pin_already_verified=True)
        if key_name not in vault:
            raise KeyError(f"Secret '{key_name}' not found in vault.")
        del vault[key_name]
        self._save_vault(vault, pin, _pin_already_verified=True)

        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        catalog["secrets"].pop(key_name, None)
        with open(CATALOG_PATH, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2)
        print(f"[SUCCESS] Secret '{key_name}' deleted from vault and catalog.")

    def list_secrets(self) -> Dict[str, Any]:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        return catalog.get("secrets", {})

    def describe_secret(self, key_name: str) -> Dict[str, Any]:
        secrets = self.list_secrets()
        if key_name not in secrets:
            raise KeyError(f"Secret '{key_name}' is not registered in the catalog.")
        return secrets[key_name]


def _has_stdin_data() -> bool:
    if sys.stdin.isatty():
        return False
    try:
        import msvcrt
        handle = msvcrt.get_osfhandle(sys.stdin.fileno())
        avail = wintypes.DWORD()
        res = ctypes.windll.kernel32.PeekNamedPipe(handle, None, 0, None, ctypes.byref(avail), None)
        return bool(res and avail.value > 0)
    except Exception:
        return False


def resolve_pin(arg_pin: Optional[str] = None, prompt_user: bool = False, try_stdin: bool = True, is_pin_configured: bool = True) -> str:
    if not is_pin_configured:
        return ""

    if arg_pin:
        return arg_pin.strip()

    env_pin = os.environ.get("VAULT_PIN")
    if env_pin:
        return env_pin.strip()

    if try_stdin and _has_stdin_data():
        piped = sys.stdin.read().strip()
        if piped:
            return piped

    if prompt_user and sys.stdin.isatty():
        return getpass.getpass("Enter Master PIN: ").strip()

    return ""


def _read_value_safely(arg_value: Optional[str]) -> str:
    if arg_value is not None:
        return arg_value

    env_val = os.environ.get("VAULT_SECRET_VALUE")
    if env_val:
        return env_val

    if _has_stdin_data():
        piped = sys.stdin.read().strip()
        if piped:
            return piped

    if sys.stdin.isatty():
        return getpass.getpass("Enter secret value: ")

    return ""


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Secure Hardware-Anchored Key Vault for AI Agents")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # set-pin
    p_pin = subparsers.add_parser("set-pin", help="Configure Master PIN (first time only)")
    p_pin.add_argument("--pin", default=None, help="Master PIN (optional: omit to enter securely)")

    # rotate-pin
    p_rotate = subparsers.add_parser("rotate-pin", help="Change Master PIN and re-encrypt vault")
    p_rotate.add_argument("--old-pin", default=None, help="Current Master PIN")
    p_rotate.add_argument("--new-pin", default=None, help="New Master PIN")

    # set
    p_set = subparsers.add_parser("set", help="Add or update a secret")
    p_set.add_argument("key", help="Key name (e.g., CLOUDFLARE_API_KEY)")
    p_set.add_argument("value", nargs="?", default=None,
                        help="Secret value (optional: omit to use VAULT_SECRET_VALUE env or stdin)")
    p_set.add_argument("--desc", default="", help="Description and purpose of the token")
    p_set.add_argument("--scope", default="general", help="Scope (read-only, admin, prod, staging)")
    p_set.add_argument("--pin", default=None, help="Master PIN (optional: omit to use VAULT_PIN or stdin)")

    # get
    p_get = subparsers.add_parser("get", help="Retrieve a secret (for JIT command injection)")
    p_get.add_argument("key", help="Key name")
    p_get.add_argument("--pin", default=None, help="Master PIN (optional)")

    # delete
    p_del = subparsers.add_parser("delete", help="Remove a secret from vault and catalog")
    p_del.add_argument("key", help="Key name")
    p_del.add_argument("--pin", default=None, help="Master PIN (optional)")

    # list
    subparsers.add_parser("list", help="List all configured secret keys and scopes (no values exposed)")

    # describe
    p_desc = subparsers.add_parser("describe", help="Get instructions and policies for a secret")
    p_desc.add_argument("key", help="Key name")

    args = parser.parse_args()
    vm = VaultManager()

    try:
        if args.command == "set-pin":
            pin = resolve_pin(args.pin, prompt_user=True, is_pin_configured=True)
            if not pin:
                print("[ERROR] Master PIN cannot be empty.", file=sys.stderr)
                sys.exit(1)
            vm.set_pin(pin)

        elif args.command == "rotate-pin":
            old_pin = args.old_pin or resolve_pin(prompt_user=True, is_pin_configured=True)
            if not old_pin:
                print("[ERROR] Current PIN cannot be empty.", file=sys.stderr)
                sys.exit(1)
            new_pin = args.new_pin or (getpass.getpass("Enter new Master PIN: ").strip() if sys.stdin.isatty() else "")
            if not new_pin:
                print("[ERROR] New PIN cannot be empty.", file=sys.stderr)
                sys.exit(1)
            vm.rotate_pin(old_pin, new_pin)

        elif args.command == "set":
            pin = resolve_pin(args.pin, prompt_user=False, try_stdin=False, is_pin_configured=vm.is_pin_set())
            value = _read_value_safely(args.value)
            if not value:
                print("[ERROR] Secret value cannot be empty.", file=sys.stderr)
                sys.exit(1)
            vm.set_secret(args.key, value, args.desc, args.scope, pin)

        elif args.command == "get":
            pin = resolve_pin(args.pin, prompt_user=False, is_pin_configured=vm.is_pin_set())
            val = vm.get_secret(args.key, pin)
            sys.stdout.write(val)

        elif args.command == "delete":
            pin = resolve_pin(args.pin, prompt_user=False, is_pin_configured=vm.is_pin_set())
            vm.delete_secret(args.key, pin)

        elif args.command == "list":
            res = vm.list_secrets()
            print(json.dumps(res, indent=2))

        elif args.command == "describe":
            res = vm.describe_secret(args.key)
            print(json.dumps(res, indent=2))

    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
