# GO Engineering Core v0.1 — Repository bootstrap

**Status:** staged standalone Python package for the future repository
`buildsmart888/go-engineering-core`. This folder is NOT yet a separate
GitHub repository. Copy the **contents** of `core_repo/` into a newly
created repository to finish the separation.

## Purpose

- One canonical steel-section identity/geometry catalog, independent of
  IngeTrazo, Qt, anaStruct, PyNite, Stabileo, and mesh renderers.
- **75** nominal GO Factory section identities; **40** have idealized
  cross-section area and strong/weak inertia suitable for *preview diagnostic*
  use (NOT certified design); **35** have no FEM properties.
- `go_engineering_core/steel_sections_v1.json` is an exact snapshot of
  the already-in-use GO Factory catalog v0.1.0.
- `go_engineering_core/catalog.py` provides pure-Python read, SHA-256,
  geometry and explicit acknowledgement helpers.
- Schema and formulas are versioned and require an explicit axis/preview
  acknowledgement; do not quietly substitute concrete profiles.

## Independence and distribution

Core is Apache-2.0 at this stage as the original GO Factory project. Check
licenses before adding external manufacturer/AISC tables. Current source is
GO Factory's own starter dimensions and legacy approximate mass estimates,
not a reproduction of a paid handbook database.

IngeTrazo plugins should remain self-contained for offline installation:
vendor a **versioned, byte-identical** snapshot into each plugin, and record
its SHA-256 in all generated member metadata. The GO Structural Analysis 3D
plugin already carries its own vetted AISC SI catalog: Core **must not**
replace it or downgrade its J/local axis/profile-source checks. A 3D handoff
must use a validated adapter and approved explicit section mapping.

## Publish the standalone repository

1. Create empty GitHub repo `buildsmart888/go-engineering-core`.
2. Copy this folder's **contents**, including `go_engineering_core/`,
   `pyproject.toml`, tests and docs, into a clean local directory.
3. Run `python -m unittest discover -s tests -v`.
4. Commit and push to the new repo. Keep v0.1.0 as a preview until
   provenance and QA are reviewed.
5. Update the two plugin vendored snapshots from that single tagged
   source. Run geometry, mass, schema and SHA-256 parity tests.

No automatic GitHub repo creation or production release has occurred.
