#!/usr/bin/env python3
"""Validates checksums in the static OpenKsenax 0.3 Maven repository."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "maven")
    required = (
        root
        / "dev"
        / "openksenax"
        / "openksenax-addon-contract"
        / "0.3.0"
        / "openksenax-addon-contract-0.3.0.aar"
    )
    if not required.is_file():
        print(f"missing contract artifact: {required}", file=sys.stderr)
        return 1

    checksum_files = sorted(root.rglob("*.sha256"))
    if not checksum_files:
        print("no SHA-256 checksum files found", file=sys.stderr)
        return 1

    failures: list[str] = []
    for checksum_file in checksum_files:
        artifact = checksum_file.with_suffix("")
        if not artifact.is_file():
            failures.append(f"missing artifact for {checksum_file}")
            continue
        expected = checksum_file.read_text(encoding="ascii").strip().lower()
        actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if expected != actual:
            failures.append(f"SHA-256 mismatch: {artifact}")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(f"validated {len(checksum_files)} Maven SHA-256 checksums")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
