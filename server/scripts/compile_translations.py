"""
Compiles all *.po files from translations/<lang>/LC_MESSAGES/
into corresponding *.mo binaries.

Supports multiple .po files per locale (e.g. base.po, authorization.po).
Each file is compiled into a separate .mo with the same name.

Usage (from server/ directory):
    python scripts/compile_translations.py
"""
import os
import sys

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po


def compile_translations(translations_root: str = None) -> None:
    if translations_root is None:
        here = os.path.dirname(os.path.abspath(__file__))
        translations_root = os.path.join(os.path.dirname(here), "translations")

    if not os.path.isdir(translations_root):
        print(f"[error] Translations directory not found: {translations_root}", file=sys.stderr)
        sys.exit(1)

    compiled = 0
    for lang in sorted(os.listdir(translations_root)):
        lc_dir = os.path.join(translations_root, lang, "LC_MESSAGES")
        if not os.path.isdir(lc_dir):
            continue

        po_files = sorted(f for f in os.listdir(lc_dir) if f.endswith(".po"))
        if not po_files:
            print(f"  [{lang}]  no .po files found")
            continue

        for po_file in po_files:
            po_path = os.path.join(lc_dir, po_file)
            mo_path = os.path.join(lc_dir, po_file.replace(".po", ".mo"))

            with open(po_path, "rb") as fh:
                catalogue = read_po(fh)

            with open(mo_path, "wb") as fh:
                write_mo(fh, catalogue)

            print(f"  [{lang}]  {po_file} -> {os.path.basename(mo_path)}  ({len(catalogue)} strings)")
            compiled += 1

    if compiled == 0:
        print("[warn] No .po files found — nothing compiled.")
    else:
        print(f"\nDone. Compiled {compiled} file(s).")


if __name__ == "__main__":
    compile_translations()