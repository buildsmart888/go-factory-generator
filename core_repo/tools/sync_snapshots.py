"""Check or update in-plugin snapshots from canonical GO Engineering Core source.

Run from a checkout of the future go-engineering-core repository OR the
initial core_repo/ staging folder. Never install an unpinned / untested change.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "go_engineering_core"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_one(label, source, destination, write=False):
    if not destination.parent.is_dir():
        raise FileNotFoundError(f"{label} plugin folder not found: {destination.parent}")
    if write:
        destination.write_bytes(source.read_bytes())
    if not destination.is_file() or source.read_bytes() != destination.read_bytes():
        raise RuntimeError(
            f"{label}: drift in {destination.name}. Vendor exact Core v0.1.0 "
            "files and run plugin tests before release."
        )
    print(f"PASS {label}: {destination.name} / sha256 {digest(destination)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--factory-package", type=Path,
                        help="Path to GO Factory's go_factory_generator/ package")
    parser.add_argument("--anastruct-package", type=Path,
                        help="Path to GO anaStruct's go_anastruct_2d/ package")
    parser.add_argument("--write", action="store_true",
                        help="Explicitly synchronize vendored copies; dry/check is default")
    args = parser.parse_args()
    targets = [
        ("Factory", args.factory_package),
        ("anaStruct", args.anastruct_package),
    ]
    if not any(path is not None for _, path in targets):
        parser.error("Provide --factory-package and/or --anastruct-package")
    for label, package in targets:
        if package is None:
            continue
        for source_name, destination_name in (
            ("catalog.py", "engineering_core.py"),
            ("steel_sections_v1.json", "steel_sections_v1.json"),
        ):
            check_one(label, CANON / source_name,
                      package / destination_name, args.write)
    print("Snapshot parity confirmed. Numerical/GUI QA is still required.")


if __name__ == "__main__":
    main()
