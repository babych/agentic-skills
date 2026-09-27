#!/usr/bin/env python3
"""
index_builder.py: Builds, cleans, sorts, and formats a publication-grade dynamic index for Typst.
"""
import sys, os, re, json

sys.stdout.reconfigure(encoding='utf-8')

UA_ALPHABET = 'абвгґдеєжзиіїйклмнопрстуфхцчшщьюя'
UA_ORDER = {ch: i for i, ch in enumerate(UA_ALPHABET)}

def ua_sort_key(s):
    s_clean = re.sub(r'^[^\w]+', '', s.lower())
    key = []
    for ch in s_clean:
        if ch in UA_ORDER:
            key.append((0, UA_ORDER[ch]))
        elif ch.isdigit():
            key.append((2, ord(ch)))
        else:
            key.append((1, ord(ch)))
    return key

def format_index_line(term, target_label=None, static_pages=None, is_sub=False):
    prefix = "#h(1em) " if is_sub else ""
    if target_label:
        page_ref = f"#context str(counter(page).at(<{target_label}>).first())"
    elif static_pages:
        page_ref = static_pages
    else:
        page_ref = "—"
    return f"{prefix}{term} #box(width: 1fr, repeat[.]) {page_ref}"
