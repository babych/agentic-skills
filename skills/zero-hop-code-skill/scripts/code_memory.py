#!/usr/bin/env python3
"""
Code Memory: Zero-dependency, 0-VRAM local BM25 & symbol search for AI coding agents.
Features incremental delta-indexing, atomic index persistence, decorator-aware AST
boundary snapping, and Zero-Hop retrieval for Cloud and Local AI coding agents.

Author: Dmytro Babych (https://github.com/babych/zero-hop-code-skill)
License: MIT (c) 2026 Dmytro Babych
"""

import sys
sys.dont_write_bytecode = True

import os
import json
import math
import re
import hashlib
import tempfile
from collections import Counter
from pathlib import Path

# Enforce UTF-8 output across Windows and POSIX shells
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

INDEX_FILE_NAME = ".code_index.json"
INDEX_VERSION = 7
MAX_FULL_SLICE_LINES = 220
FULL_SLICE_HEAD_LINES = 200
MAX_LINE_DISPLAY_CHARS = 500

DEFAULT_EXTS = {
    ".js", ".ts", ".jsx", ".tsx", ".vue", ".html", ".css",
    ".py", ".sql", ".dart", ".cs", ".go", ".rs", ".java", ".kt",
    ".cpp", ".c", ".h", ".hpp", ".php", ".rb", ".swift"
}

DEFAULT_IGNORE_DIRS = {
    ".git", "node_modules", ".gemini", ".cursor", ".windsurf", ".claude", ".aider", ".agent",
    "dist", "build", "out", "target", "vendor", "coverage",
    ".wrangler", "__pycache__", ".venv", "venv", "env",
    "bin", "obj", ".vs", ".idea", ".dart_tool", ".pub-cache", ".next", ".nuxt"
}

IGNORE_FILE_SUFFIXES = (
    ".min.js", ".min.css", ".bundle.js", ".map",
    ".g.cs", ".designer.cs", ".generated.cs", ".assemblyinfo.cs",
    ".g.dart", ".freezed.dart", ".gr.dart",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "composer.lock", "cargo.lock"
)

WIN_RESERVED_STEMS = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}

# Type definitions (class, interface, enum, struct, record, mixin, extension, trait, TS type, Rust impl)
TYPE_DEF_PATTERN = re.compile(
    r'^\s*(?:export\s+)?(?:default\s+)?(?:public\s+|private\s+|protected\s+|internal\s+|fileprivate\s+|open\s+)?'
    r'(?:abstract\s+|sealed\s+|static\s+|partial\s+|base\s+|final\s+|data\s+|value\s+|readonly\s+|ref\s+)*'
    r'(?:(?:class|interface|enum|struct|record(?:\s+struct|\s+class)?|mixin|extension|typedef|trait|type|protocol)\s+([A-Za-z_][A-Za-z0-9_]*)'
    r'|impl(?:<[^>]+>)?\s+(?:[A-Za-z_][A-Za-z0-9_:<>,\s]*?\s+for\s+)?([A-Za-z_][A-Za-z0-9_]*))'
)

# Method / Function definitions across TS/JS, Python, Rust, Go, C#, Java, Kotlin, Dart, C/C++, PHP, Swift, Ruby
FUNC_DEF_PATTERN = re.compile(
    r'^\s*(?:'
    # 1. JS/TS/PHP function keyword
    r'(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:<[^>]+>)?\s*\('
    # 2. JS/TS arrow / const function: export const foo = async (...) =>
    r'|(?:export\s+)?(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::[^=]+)?=\s*(?:async\s*)?(?:<[^>]+>)?\s*\([^)]*\)\s*(?::[^=]+)?=>'
    # 3. Python def / async def
    r'|(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\('
    # 4. Rust fn
    r'|(?:pub(?:\s*\([^)]+\))?\s+)?(?:async\s+)?(?:unsafe\s+)?(?:extern\s+"[^"]+"\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:<[^>]+>)?\s*\('
    # 5. Go func
    r'|func\s+(?:\([^)]+\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[[^\]]+\])?\s*\('
    # 6. Ruby def
    r'|def\s+(?:self\.)?([A-Za-z_][A-Za-z0-9_!?=]*)'
    # 7. Typed C#/Java/Kotlin/Dart/C++/Swift methods (with return type, pointer, or tuple return)
    r'|(?:(?:public|private|protected|internal|fileprivate|open|static|async|override|virtual|abstract|sealed|extern|inline|constexpr|suspend|fun|Future|Task|Widget|void|int|long|double|float|bool|boolean|String|string|char|var|final|const)\b\s+)+'
    r'(?:(?:\([^)]+\)|[A-Za-z_][A-Za-z0-9_<>,.\[\]?]*)(?:\s*\*+\s*|\s+))?'
    r'([A-Za-z_][A-Za-z0-9_]*)\s*(?:<[^>]+>)?\s*\('
    # 8. JS/TS/Dart unprefixed class methods / getters / setters: async foo(...) { or foo(...): Bar {
    r'|(?:async\s+|get\s+|set\s+|static\s+|readonly\s+)*([A-Za-z_][A-Za-z0-9_]*)\s*(?:<[^>]+>)?\s*\([^;{}]*\)\s*(?::\s*[^{=;]+)?\s*\{'
    r')'
)

SQL_DEF_PATTERN = re.compile(
    r'^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:UNIQUE\s+)?(?:TABLE|VIEW|PROCEDURE|PROC|FUNCTION|TRIGGER|INDEX)\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z0-9_."\[\]]+)',
    re.IGNORECASE
)

# Strips verbatim/raw/triple strings, standard strings, regex literals, and block/line comments
STRING_OR_COMMENT_RE = re.compile(
    r'@"(?:""|[^"])*"'                  # C# verbatim string
    r'|"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\''  # Python / C# raw triple-quoted strings
    r'|/\*[\s\S]*?\*/'                    # Block comments
    r'|`(?:\\.|[^`\\])*`'                 # JS/TS template literals
    r'|"(?:\\.|[^"\\])*"'                 # Double-quoted strings
    r'|\'(?:\\.|[^\'\\])*\''              # Single-quoted strings
    r'|//.*?$|#.*?$',                     # Single-line comments
    re.MULTILINE
)

CONTROL_KEYWORDS = {
    "if", "for", "foreach", "while", "switch", "catch", "using", "lock",
    "return", "throw", "new", "await", "typeof", "nameof", "sizeof",
    "super", "this", "else", "elif", "when", "match", "assert"
}

STOP_WORDS = {
    "the", "and", "for", "with", "this", "that", "from", "return",
    "public", "private", "protected", "internal", "static", "async",
    "await", "void", "null", "true", "false", "new", "try", "catch",
    "else", "elif"
}


def light_stem(token):
    """Lightweight suffix normalization for English technical identifiers."""
    if len(token) < 5:
        return token
    if token.endswith("ies") and len(token) > 5:
        return token[:-3] + "y"
    if token.endswith("ing") and len(token) > 6:
        return token[:-3]
    if token.endswith("ed") and len(token) > 5:
        return token[:-2]
    if token.endswith("es") and len(token) > 5:
        return token[:-2]
    if token.endswith("s") and not token.endswith("ss") and len(token) > 4:
        return token[:-1]
    return token


def tokenize(text, remove_stopwords=True, include_stems=True):
    """Splits camelCase, PascalCase, ACRONYMS, snake_case, and multilingual words."""
    text = re.sub(r'([A-Z\u0410-\u042F]+)([A-Z\u0410-\u042F][a-z\u0430-\u044F])', r'\1 \2', text)
    text = re.sub(r'([a-z0-9\u0430-\u044F])([A-Z\u0410-\u042F])', r'\1 \2', text)
    text = text.replace('_', ' ').replace('-', ' ')
    raw_tokens = re.findall(r'[a-zA-Z0-9\u0400-\u04FF]+', text.lower())
    out = []
    for t in raw_tokens:
        if len(t) <= 1 and not t.isalpha():
            continue
        if len(t) == 1 and t not in ("x", "y", "z", "t", "k", "v"):
            continue
        if remove_stopwords and t in STOP_WORDS:
            continue
        out.append(t)
        if include_stems:
            st = light_stem(t)
            if st != t:
                out.append(st)
    return out


def extract_symbols_and_def_lines(lines, suffix=""):
    def_lines = set()
    type_def_lines = set()
    line_symbols = {}
    n_lines = len(lines)

    for idx in range(n_lines):
        stripped = lines[idx].strip()
        if not stripped or stripped.startswith(("//", "#", "/*", "*", "///", "--")):
            continue

        # 3-line lookahead window handles wrapped multi-line method signatures
        window = "\n".join(lines[idx:min(n_lines, idx + 3)])
        found_names = []

        if suffix == ".sql":
            m_sql = SQL_DEF_PATTERN.match(stripped)
            if m_sql:
                found_names.append(m_sql.group(1).strip('[]"'))
        else:
            m_type = TYPE_DEF_PATTERN.match(stripped)
            if m_type:
                t_name = next((g for g in m_type.groups() if g is not None), None)
                if t_name:
                    found_names.append(t_name)
                    type_def_lines.add(idx)

            m_func = FUNC_DEF_PATTERN.match(window)
            if m_func:
                name = next((g for g in m_func.groups() if g is not None), None)
                if name and name not in CONTROL_KEYWORDS and name.lower() not in CONTROL_KEYWORDS:
                    found_names.append(name)

        if found_names:
            def_lines.add(idx)
            sym_tokens = []
            for name in found_names:
                sym_tokens.extend(tokenize(name, remove_stopwords=False, include_stems=True))
                sym_tokens.append(name.lower())
            line_symbols[idx] = list(set(sym_tokens))

    return sorted(def_lines), type_def_lines, line_symbols


def include_leading_decorators(lines, def_idx):
    """Captures stacked decorators, attributes, multi-line @router(...) calls, and doc comments."""
    start = def_idx
    paren_balance = 0
    for back in range(1, 13):
        cand = def_idx - back
        if cand < 0:
            break
        s = lines[cand].strip()
        if not s:
            if paren_balance == 0:
                break
            start = cand
            continue
        if s in ("{", "}") or s.endswith(";"):
            break

        paren_balance += s.count(")") - s.count("(")
        if paren_balance > 0 or s.startswith(("@", "[", "///", "/**", "//", "#")):
            start = cand
        else:
            break
    return start


def compute_smart_end_line(lines, start_line, def_idx, def_set, is_python=False, is_type_def=False):
    """
    Finds natural logical boundaries without swallowing inner class methods,
    expression-bodied C# members, interface declarations, or single-line functions.
    """
    n_lines = len(lines)
    if start_line >= n_lines:
        return n_lines

    if is_python and def_idx < n_lines:
        base_indent = len(lines[def_idx].expandtabs(4)) - len(lines[def_idx].expandtabs(4).lstrip())
        sig_closed = False
        paren_depth = 0
        for idx in range(def_idx, n_lines):
            raw = lines[idx]
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            clean = STRING_OR_COMMENT_RE.sub("", stripped)
            paren_depth += clean.count("(") + clean.count("[") - clean.count(")") - clean.count("]")
            if not sig_closed:
                if paren_depth <= 0 and clean.rstrip().endswith(":"):
                    sig_closed = True
                    # Single-line def: `def foo(): return 1`
                    after_colon = clean.split(":", 1)[1].strip()
                    if after_colon:
                        return idx + 1
                continue

            curr_indent = len(raw.expandtabs(4)) - len(raw.expandtabs(4).lstrip())
            if curr_indent <= base_indent:
                return include_leading_decorators(lines, idx)
        return n_lines

    # Brace-delimited & declaration-based languages
    brace_balance = 0
    paren_balance = 0
    saw_open_brace = False

    def _strip_keep_newlines(m):
        return "\n" * m.group(0).count("\n")

    full_text = "\n".join(lines[start_line:])
    clean_text = STRING_OR_COMMENT_RE.sub(_strip_keep_newlines, full_text)
    clean_lines = clean_text.splitlines()

    for offset, clean_line in enumerate(clean_lines):
        idx = start_line + offset

        # For class/interface definitions, stop at the first inner method so methods get their own chunks
        if is_type_def and idx > def_idx and idx in def_set:
            return include_leading_decorators(lines, idx)

        # Only break at another top-level definition when braces are balanced (never mid-method on nested closures)
        if idx > def_idx and brace_balance == 0 and idx in def_set:
            return include_leading_decorators(lines, idx)

        paren_balance += clean_line.count("(") - clean_line.count(")")
        open_c = clean_line.count("{")
        close_c = clean_line.count("}")
        if open_c > 0:
            saw_open_brace = True
        brace_balance += (open_c - close_c)

        # Single-line semicolon-terminated signature (interface method, C# primary-ctor record, abstract method)
        if not saw_open_brace and paren_balance <= 0 and clean_line.rstrip().endswith(";"):
            return idx + 1

        if saw_open_brace and brace_balance <= 0:
            return idx + 1

    return n_lines


def find_repo_root(start_dir="."):
    """Walks upward to locate the nearest .git directory/file if present."""
    p = Path(start_dir).resolve()
    for candidate in (p, *p.parents):
        if (candidate / ".git").exists():
            return candidate
    return p


def resolve_index_path(root, use_temp_index=False):
    if use_temp_index:
        digest = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:16]
        return Path(tempfile.gettempdir()) / f"code_index_{digest}.json"
    return root / INDEX_FILE_NAME


def iter_source_files(root_dir=".", ext_filter=None):
    root = Path(root_dir).resolve()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [
            d for d in dirnames
            if d not in DEFAULT_IGNORE_DIRS and not d.startswith(".git")
        ]
        for fname in filenames:
            if fname == INDEX_FILE_NAME:
                continue
            lower_fname = fname.lower()
            if lower_fname.endswith(IGNORE_FILE_SUFFIXES):
                continue
            fpath = Path(dirpath) / fname
            if fpath.is_symlink():
                continue
            if sys.platform == "win32" and fpath.stem.lower() in WIN_RESERVED_STEMS:
                continue
            ext = fpath.suffix.lower()
            if ext not in DEFAULT_EXTS:
                continue
            if ext_filter and ext not in ext_filter:
                continue
            yield fpath, root


def ensure_git_exclude(root):
    """Updates .git/info/exclude (including worktrees) in pure Python without subprocesses."""
    try:
        git_entry = root / ".git"
        if not git_entry.exists():
            return
        if git_entry.is_file():
            # Git worktree or submodule pointer: `gitdir: <path>`
            text = git_entry.read_text(encoding="utf-8", errors="ignore").strip()
            if text.startswith("gitdir:"):
                git_dir = (root / text.split(":", 1)[1].strip()).resolve()
            else:
                return
        else:
            git_dir = git_entry

        exclude_file = git_dir / "info" / "exclude"
        exclude_file.parent.mkdir(parents=True, exist_ok=True)
        content = exclude_file.read_text(encoding="utf-8", errors="ignore") if exclude_file.exists() else ""
        if INDEX_FILE_NAME not in content.splitlines():
            with exclude_file.open("a", encoding="utf-8") as f:
                prefix = "\n" if content and not content.endswith("\n") else ""
                f.write(f"{prefix}{INDEX_FILE_NAME}\n")
    except Exception:
        pass


def chunk_single_file(path, rel_path):
    file_chunks = []
    try:
        content = path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception as e:
        print(f"⚠️ Warning: Failed to read {rel_path}: {e}", file=sys.stderr)
        return file_chunks

    lines = content.splitlines()
    n_lines = len(lines)
    if n_lines == 0:
        return file_chunks

    # Skip un-suffixed minified bundles (avg line length > 500 chars)
    if len(content) / max(1, n_lines) > 500:
        return file_chunks

    suffix = path.suffix.lower()
    is_python = suffix == ".py"
    def_indices, type_def_lines, line_symbols = extract_symbols_and_def_lines(lines, suffix=suffix)
    def_set = set(def_indices)

    if not def_indices:
        step = 50
        i = 0
        while i < n_lines:
            start_line = i
            end_line = min(n_lines, start_line + 80)
            chunk_lines = lines[start_line:end_line]
            if chunk_lines:
                chunk_text = "\n".join(chunk_lines)
                code_only = STRING_OR_COMMENT_RE.sub(" ", chunk_text)
                if code_only.strip():
                    tf = Counter(tokenize(chunk_text))
                    if tf:
                        file_chunks.append({
                            "file": rel_path,
                            "start_line": start_line + 1,
                            "end_line": end_line,
                            "total_lines": n_lines,
                            "truncated": end_line < n_lines,
                            "tf": dict(tf),
                            "symbols": [],
                            "header": chunk_lines[0].strip()[:120]
                        })
            i += step
        return file_chunks

    processed_ranges = []
    for def_idx in def_indices:
        start_line = include_leading_decorators(lines, def_idx)
        if processed_ranges and start_line < processed_ranges[-1]:
            continue

        is_type = def_idx in type_def_lines
        end_line = compute_smart_end_line(
            lines, start_line, def_idx, def_set, is_python=is_python, is_type_def=is_type
        )
        processed_ranges.append(end_line)

        chunk_lines = lines[start_line:end_line]
        if chunk_lines:
            chunk_text = "\n".join(chunk_lines)
            tf = Counter(tokenize(chunk_text))
            symbols = []
            for line_idx in range(start_line, end_line):
                if line_idx in line_symbols:
                    symbols.extend(line_symbols[line_idx])
            unique_syms = list(set(symbols))
            for s in unique_syms:
                tf[s] = max(tf.get(s, 0), 2)

            if tf:
                sig_line = lines[def_idx].strip()[:120]
                file_chunks.append({
                    "file": rel_path,
                    "start_line": start_line + 1,
                    "end_line": end_line,
                    "total_lines": n_lines,
                    "truncated": False,
                    "tf": dict(tf),
                    "symbols": unique_syms,
                    "header": sig_line
                })

    return file_chunks


def atomic_write_json(target_path, payload):
    """Writes JSON atomically via temp file + os.replace to prevent parallel corruption."""
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(target_path.parent), prefix=".tmp_code_idx_")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            os.replace(tmp_name, target_path)
        except Exception:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
            raise
    except OSError:
        # Gracefully tolerate read-only workspaces
        pass


def build_or_update_index(root_dir=".", force_full=False, quiet=False, use_temp_index=False):
    root = Path(root_dir).resolve()
    if not root.is_dir():
        print(f"❌ Directory not found: {root_dir}", file=sys.stderr)
        return []

    index_path = resolve_index_path(root, use_temp_index=use_temp_index)
    existing_file_sigs = {}
    existing_chunks_by_file = {}

    if not force_full and index_path.exists():
        try:
            raw = json.loads(index_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and raw.get("version") == INDEX_VERSION:
                existing_file_sigs = raw.get("file_sigs", {})
                for ch in raw.get("chunks", []):
                    existing_chunks_by_file.setdefault(ch["file"], []).append(ch)
        except Exception:
            pass

    new_file_sigs = {}
    all_chunks = []
    reindexed_count = 0

    for path, _ in iter_source_files(root):
        try:
            stat = path.stat(follow_symlinks=False)
            if stat.st_size > 5 * 1024 * 1024:
                if not quiet:
                    print(f"⚠️ Skipping large file (>5MB): {path.relative_to(root)}", file=sys.stderr)
                continue
            rel_path = path.relative_to(root).as_posix()
            sig = [round(stat.st_mtime, 3), stat.st_size]
            new_file_sigs[rel_path] = sig

            if (
                not force_full
                and rel_path in existing_file_sigs
                and existing_file_sigs[rel_path] == sig
                and rel_path in existing_chunks_by_file
            ):
                all_chunks.extend(existing_chunks_by_file[rel_path])
            else:
                all_chunks.extend(chunk_single_file(path, rel_path))
                reindexed_count += 1
        except Exception as e:
            if not quiet:
                print(f"⚠️ Error processing {path}: {e}", file=sys.stderr)

    deleted_files = set(existing_file_sigs.keys()) - set(new_file_sigs.keys())
    if all_chunks and (reindexed_count > 0 or deleted_files or force_full or not index_path.exists()):
        meta = {
            "version": INDEX_VERSION,
            "file_sigs": new_file_sigs,
            "chunks": all_chunks
        }
        atomic_write_json(index_path, meta)
        if not use_temp_index:
            ensure_git_exclude(root)
        if not quiet:
            print(f"✅ Indexed {len(all_chunks)} chunks across {len(new_file_sigs)} files ({reindexed_count} updated).")
    elif not quiet:
        print(f"✅ Index is already up-to-date ({len(all_chunks)} chunks).")

    return all_chunks


def extract_chunk_view(root_dir, file_rel_path, start_line, end_line, query_tokens, full_slice=False, fallback_header=""):
    fpath = Path(root_dir) / file_rel_path
    try:
        lines = fpath.read_text(encoding="utf-8-sig", errors="ignore").splitlines()
        chunk_lines = lines[start_line - 1:end_line]
        if not chunk_lines:
            return [(start_line, fallback_header)], False

        if full_slice:
            was_clamped = False
            display_lines = chunk_lines
            if len(chunk_lines) > MAX_FULL_SLICE_LINES:
                display_lines = chunk_lines[:FULL_SLICE_HEAD_LINES]
                was_clamped = True

            out = []
            for idx, text in enumerate(display_lines):
                clean = text.rstrip("\r\n")
                if len(clean) > MAX_LINE_DISPLAY_CHARS:
                    clean = f"{clean[:MAX_LINE_DISPLAY_CHARS]} ... [line truncated at {MAX_LINE_DISPLAY_CHARS} of {len(clean)} chars]"
                out.append((start_line + idx, clean))
            return out, was_clamped

        scored_lines = []
        for idx, text in enumerate(chunk_lines):
            line_num = start_line + idx
            line_tokens = set(tokenize(text, remove_stopwords=False))
            hits = len(query_tokens.intersection(line_tokens))
            scored_lines.append((hits, idx, line_num, text.strip()))

        best_hits, best_idx, _, _ = max(scored_lines, key=lambda x: x[0])

        preview = []
        seen_lines = set()

        def _add_preview(idx_in_chunk):
            if 0 <= idx_in_chunk < len(chunk_lines) and idx_in_chunk not in seen_lines:
                l_text = chunk_lines[idx_in_chunk].strip()
                if l_text:
                    seen_lines.add(idx_in_chunk)
                    preview.append((start_line + idx_in_chunk, l_text[:110]))

        _add_preview(0)
        # Ensure signature line is shown if chunk starts with decorators
        for idx, text in enumerate(chunk_lines[:12]):
            if fallback_header and text.strip().startswith(fallback_header[:40]):
                _add_preview(idx)
                break

        if best_hits > 0:
            for idx in range(max(0, best_idx - 1), min(len(chunk_lines), best_idx + 2)):
                _add_preview(idx)
        else:
            for idx in range(1, min(4, len(chunk_lines))):
                _add_preview(idx)

        return preview[:4], False
    except Exception:
        return [(start_line, fallback_header)], False


def classify_reference_line(line):
    s = line.strip()
    if s.startswith(("//", "#", "/*", "*", "///", "--")):
        return "COMMENT/STR"
    if TYPE_DEF_PATTERN.match(s) or FUNC_DEF_PATTERN.match(s):
        return "DEF"
    return "CODE"


def search_references(symbol, root_dir=".", context_lines=0, ext_filter=None):
    """Finds every whole-word occurrence of a symbol across source files."""
    root = Path(root_dir).resolve()
    if not root.is_dir():
        print(f"❌ Directory not found: {root_dir}", file=sys.stderr)
        return

    pattern = re.compile(rf'\b{re.escape(symbol)}\b')
    grouped = {"DEF": [], "CODE": [], "COMMENT/STR": []}

    for path, _ in iter_source_files(root, ext_filter=ext_filter):
        try:
            rel_path = path.relative_to(root).as_posix()
            lines = path.read_text(encoding="utf-8-sig", errors="ignore").splitlines()
            for idx, line in enumerate(lines):
                if pattern.search(line):
                    kind = classify_reference_line(line)
                    ctx = []
                    if context_lines > 0:
                        lo = max(0, idx - context_lines)
                        hi = min(len(lines), idx + context_lines + 1)
                        ctx = [(i + 1, lines[i].rstrip("\r\n")[:110]) for i in range(lo, hi)]
                    grouped[kind].append((rel_path, idx + 1, line.strip()[:110], ctx))
        except Exception:
            pass

    total = sum(len(v) for v in grouped.values())
    print(f"\n🔍 All whole-word references for: '{symbol}' ({total} matches)\n---")
    for kind in ("DEF", "CODE", "COMMENT/STR"):
        items = grouped[kind]
        if not items:
            continue
        print(f"[{kind}] ({len(items)})")
        for rel_path, line_no, text, ctx in items:
            print(f"📍 {rel_path} | L{line_no}|{text}")
            for c_no, c_text in ctx:
                if c_no != line_no:
                    print(f"   L{c_no}|{c_text}")
    print("---")


def search(
    query,
    top_k=3,
    mode="smart",
    root_dir=".",
    token_budget=1200,
    ext_filter=None,
    use_temp_index=False,
    as_json=False
):
    root = Path(root_dir).resolve()
    if not root.is_dir():
        print(f"❌ Directory not found: {root_dir}", file=sys.stderr)
        return

    chunks = build_or_update_index(root, force_full=False, quiet=True, use_temp_index=use_temp_index)
    if ext_filter:
        chunks = [c for c in chunks if Path(c["file"]).suffix.lower() in ext_filter]

    # Strip stack-trace line suffixes like `auth.ts:42`
    cleaned_query = re.sub(r':\d+\b', '', query).strip()
    query_tokens = set(tokenize(cleaned_query, remove_stopwords=True, include_stems=True))
    if not query_tokens:
        query_tokens = set(tokenize(cleaned_query, remove_stopwords=False, include_stems=True))

    # Preserve raw lowercased identifiers (e.g. `verifyRefreshToken` -> `verifyrefreshtoken`)
    raw_idents = {w.lower() for w in re.findall(r'[A-Za-z_][A-Za-z0-9_]{2,}', cleaned_query)}
    query_tokens.update(raw_idents)

    # Support `Class.method` or `Namespace::method` dot/colon qualifiers
    qualifier_prefix = None
    m_qual = re.search(r'([A-Za-z_][A-Za-z0-9_]*)(?:\.|::)([A-Za-z_][A-Za-z0-9_]*)', cleaned_query)
    if m_qual:
        qualifier_prefix = m_qual.group(1).lower()

    if not query_tokens:
        print("❌ Query is empty.")
        return

    n_chunks = max(1, len(chunks))
    total_doc_len = 0
    doc_freq = Counter()

    for chunk in chunks:
        tf = chunk.get("tf")
        if tf is None:
            # Backward-compatible fallback if reading an older structure
            tf = {w: 1 for w in chunk.get("words", [])}
            chunk["tf"] = tf
        total_doc_len += sum(tf.values())
        for qt in query_tokens:
            if qt in tf:
                doc_freq[qt] += 1

    avgdl = max(1.0, total_doc_len / n_chunks)
    k1 = 1.5
    b = 0.75

    idf = {
        qt: math.log(1.0 + (n_chunks - doc_freq[qt] + 0.5) / (doc_freq[qt] + 0.5))
        for qt in query_tokens
    }

    scored = []
    for chunk in chunks:
        tf = chunk["tf"]
        chunk_symbols = set(chunk.get("symbols", []))
        matched_words = [qt for qt in query_tokens if qt in tf]
        matched_symbols = query_tokens.intersection(chunk_symbols)

        if matched_words or matched_symbols:
            dl = max(1, sum(tf.values()))
            bm25_score = 0.0
            for qt in matched_words:
                freq = tf[qt]
                denom = freq + k1 * (1.0 - b + b * (dl / avgdl))
                bm25_score += idf[qt] * ((freq * (k1 + 1.0)) / denom)

            if matched_symbols:
                sym_idf_sum = sum(idf.get(qt, 2.0) for qt in matched_symbols)
                bm25_score += sym_idf_sum * 1.8

            path_tokens = set(tokenize(chunk["file"], remove_stopwords=False, include_stems=True))
            for qt in query_tokens:
                if qt in path_tokens:
                    bm25_score += idf.get(qt, 1.0) * 0.5

            if qualifier_prefix and (qualifier_prefix in path_tokens or qualifier_prefix in chunk_symbols):
                bm25_score *= 1.35

            header_lower = chunk.get("header", "").lower()
            if all(qt in header_lower for qt in raw_idents):
                bm25_score *= 1.25

            coverage = len(set(matched_words).union(matched_symbols)) / len(query_tokens)
            bm25_score *= (1.0 + 0.5 * coverage)

            scored.append((bm25_score, coverage, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)

    selected = []
    for score, coverage, chunk in scored:
        is_overlapping = False
        for _, _, existing in selected:
            if existing["file"] == chunk["file"]:
                overlap = min(existing["end_line"], chunk["end_line"]) - max(existing["start_line"], chunk["start_line"])
                if overlap > 0:
                    is_overlapping = True
                    break
        if not is_overlapping:
            selected.append((score, coverage, chunk))
        if len(selected) >= top_k:
            break

    if not selected:
        if as_json:
            print(json.dumps({"query": query, "results": []}))
        else:
            print(f"🔍 No matching code found for: '{query}'")
        return

    used_tokens = 0
    full_file_tokens_est = 0
    seen_files_for_est = set()
    json_results = []

    if not as_json:
        print(f"\n🔍 Top {len(selected)} relevant code locations for: '{query}'\n---")

    for rank, (score, coverage, item) in enumerate(selected):
        total_l = item.get("total_lines", 0)
        slice_len = max(1, item["end_line"] - item["start_line"] + 1)
        est_slice_tokens = slice_len * 10

        if mode == "full":
            show_full = True
        elif mode == "brief":
            show_full = False
        else:
            if rank == 0:
                show_full = True
            elif token_budget > 0 and (used_tokens + est_slice_tokens) <= token_budget:
                show_full = True
            else:
                show_full = False

        view_lines, was_clamped = extract_chunk_view(
            root, item["file"], item["start_line"], item["end_line"],
            query_tokens, full_slice=show_full, fallback_header=item.get("header", "")
        )

        emitted_chars = sum(len(t) for _, t in view_lines)
        used_tokens += max(1, emitted_chars // 4)
        if item["file"] not in seen_files_for_est and isinstance(total_l, int):
            seen_files_for_est.add(item["file"])
            full_file_tokens_est += total_l * 10

        tags = []
        if show_full:
            if item.get("truncated"):
                tags.append("[TOP MATCH - PARTIAL WINDOW]" if rank == 0 else "[PARTIAL WINDOW]")
            elif was_clamped:
                tags.append(f"[TRUNCATED AT {FULL_SLICE_HEAD_LINES} OF {slice_len} LINES]")
            elif rank == 0:
                tags.append("[TOP MATCH - FULL SLICE]")
            else:
                tags.append("[FULL SLICE]")
        if coverage < 0.5 and score < 0.6:
            tags.append("[LOW CONFIDENCE]")

        tag_str = (" " + " ".join(tags)) if tags else ""

        if as_json:
            json_results.append({
                "file": item["file"],
                "start_line": item["start_line"],
                "end_line": item["end_line"],
                "total_lines": total_l,
                "score": round(score, 3),
                "coverage": round(coverage, 3),
                "full_slice": show_full,
                "truncated": bool(item.get("truncated") or was_clamped),
                "lines": [{"line": ln, "text": txt} for ln, txt in view_lines]
            })
        else:
            print(
                f"📍 {item['file']} (Lines {item['start_line']} - {item['end_line']} of {total_l})"
                f" [Score: {score:.2f}]{tag_str}"
            )
            for line_no, text in view_lines:
                print(f"L{line_no}|{text}")
            if was_clamped:
                rem_start = item["start_line"] + FULL_SLICE_HEAD_LINES
                print(f"... [Read lines L{rem_start}-L{item['end_line']} for remainder]")
            print("---")

    if as_json:
        print(json.dumps({"query": query, "results": json_results}, ensure_ascii=False, indent=2))
    elif full_file_tokens_est > 0:
        print(f"Returned {len(selected)} chunks (~{used_tokens:,} tokens vs ~{full_file_tokens_est:,} tokens for full files)")


def normalize_ext_filter(raw_ext):
    if not raw_ext:
        return None
    exts = set()
    for part in raw_ext.split(","):
        p = part.strip().lower()
        if p:
            exts.add(p if p.startswith(".") else f".{p}")
    return exts or None


def parse_cli_args(argv):
    top_k = 3
    mode = "smart"
    root_dir = None
    token_budget = 1200
    context_lines = 0
    ext_filter = None
    use_temp_index = False
    as_json = False
    query_parts = []

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--":
            query_parts.extend(argv[i + 1:])
            break
        elif arg in ("--top", "-k") and i + 1 < len(argv):
            try:
                top_k = max(1, int(argv[i + 1]))
            except ValueError:
                print(f"⚠️ Invalid --top value '{argv[i + 1]}', using default {top_k}.", file=sys.stderr)
            i += 2
        elif arg in ("--budget", "-b") and i + 1 < len(argv):
            try:
                token_budget = max(0, int(argv[i + 1]))
            except ValueError:
                pass
            i += 2
        elif arg in ("--context", "-C") and i + 1 < len(argv):
            try:
                context_lines = max(0, int(argv[i + 1]))
            except ValueError:
                pass
            i += 2
        elif arg in ("--ext", "-e") and i + 1 < len(argv):
            ext_filter = normalize_ext_filter(argv[i + 1])
            i += 2
        elif arg in ("--path", "-p") and i + 1 < len(argv):
            root_dir = argv[i + 1].rstrip('"\\')
            i += 2
        elif arg == "--brief":
            mode = "brief"
            i += 1
        elif arg == "--full":
            mode = "full"
            i += 1
        elif arg == "--smart":
            mode = "smart"
            i += 1
        elif arg == "--temp-index":
            use_temp_index = True
            i += 1
        elif arg == "--local-index":
            use_temp_index = False
            i += 1
        elif arg == "--json":
            as_json = True
            i += 1
        else:
            query_parts.append(arg)
            i += 1

    resolved_root = Path(root_dir).resolve() if root_dir else find_repo_root(".")
    return {
        "query": " ".join(query_parts),
        "top_k": top_k,
        "mode": mode,
        "root_dir": resolved_root,
        "token_budget": token_budget,
        "context_lines": context_lines,
        "ext_filter": ext_filter,
        "use_temp_index": use_temp_index,
        "as_json": as_json,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(f"Code Memory (index v{INDEX_VERSION}) - Zero-VRAM BM25 & Symbol Search\n")
        print("Usage:")
        print("  python3 code_memory.py search <query> [--top 3] [--budget 1200] [--brief|--full] [--ext .ts] [--path .] [--json]")
        print("  python3 code_memory.py refs <symbol> [--context 1] [--ext .ts] [--path .]")
        print("  python3 code_memory.py index [path] [--temp-index]")
        print("  python3 code_memory.py test")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "test":
        import unittest
        tests_dir = Path(__file__).resolve().parent.parent / "tests"
        if not tests_dir.exists():
            tests_dir = Path("tests")
        suite = unittest.defaultTestLoader.discover(str(tests_dir), pattern="test_*.py")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)
    elif cmd == "index":
        opts = parse_cli_args(sys.argv[2:])
        target = opts["query"] if opts["query"] and os.path.isdir(opts["query"]) else opts["root_dir"]
        build_or_update_index(target, force_full=True, quiet=False, use_temp_index=opts["use_temp_index"])
    elif cmd == "refs":
        opts = parse_cli_args(sys.argv[2:])
        if opts["query"]:
            search_references(
                opts["query"],
                root_dir=opts["root_dir"],
                context_lines=opts["context_lines"],
                ext_filter=opts["ext_filter"]
            )
        else:
            print("❌ Please specify a symbol to find references for.")
    elif cmd == "search":
        opts = parse_cli_args(sys.argv[2:])
        search(
            opts["query"],
            top_k=opts["top_k"],
            mode=opts["mode"],
            root_dir=opts["root_dir"],
            token_budget=opts["token_budget"],
            ext_filter=opts["ext_filter"],
            use_temp_index=opts["use_temp_index"],
            as_json=opts["as_json"]
        )
    else:
        opts = parse_cli_args(sys.argv[1:])
        search(
            opts["query"],
            top_k=opts["top_k"],
            mode=opts["mode"],
            root_dir=opts["root_dir"],
            token_budget=opts["token_budget"],
            ext_filter=opts["ext_filter"],
            use_temp_index=opts["use_temp_index"],
            as_json=opts["as_json"]
        )
