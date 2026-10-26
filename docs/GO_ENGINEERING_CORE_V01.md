# GO Engineering Core v0.1 — Shared Steel Section Catalog

**Status: preview only. No manufacturer-verified A, I, J, Fy, or design resistances.**

This module is a first integration toward a solver-independent Core used by
GO Factory, GO anaStruct and, later, GO Structural Analysis 3D.

## Current source of truth

The existing GO Factory Generator v0.3.1 starter steel library was transformed
into a versioned, portable JSON schema (`go-steel-sections/1`).

Both integration branches contain exactly the same two files:

- `engineering_core.py` — pure Python, no Qt/IngeTrazo/anaStruct dependency
- `steel_sections_v1.json` — 75 section IDs, nominal dimensions and legacy approximate kg/m

The snapshot is packaged inside **each** IngeTrazo plugin to preserve offline
installation. The generated GO Factory member metadata includes section ID,
Core version, SHA-256 of the exact catalog, property status and legacy mass status.
GO anaStruct checks the catalog version/hash during import and rejects
conflicting snapshots. Old untagged GO Factory scenes remain supported, but
display a warning that the catalog origin was not pinned.

A dedicated standalone `go-engineering-core` GitHub repository is an intended
follow-up. For now, the Factory branch is the source of the v0.1 snapshot and the
anaStruct branch is an exact vendored copy. **Do not edit the two copies independently**;
when the catalog changes, increment its version and synchronize both copies.

## Properties and limits

- 75 exact GO Factory starter-section names
- 40 H/WF, RHS/SHS and round-pipe profiles with idealized *nominal* area and
  major/minor second moments of area. The user must pick the section bending axis.
- 35 other profiles (C/Z/angles/bars/plates) are kept for geometry and takeoff
  identification but have NO auto-generated FEM stiffness: geometry source and
  analysis-axis information are not yet complete.
- Nominal formulas use sharp-corner rectangles and thin idealized H flanges.
  Real rolling radii, welded details, tolerances, thickness reductions and
  net-section effective properties have not been included.
- The original GO Factory mass values remain **approximate legacy takeoff**.
  The Core provides a separate diagnostic mass estimate from A × 7,850 kg/m³;
  neither value is validated for procurement.
- The Core does not invent a steel grade, Fy/Fu or a 3D member-axis orientation.
  GO anaStruct uses the existing explicitly selected material E and rho.
- Any property with status `NOMINAL_GEOMETRY_ONLY` must **not** be used to
  certify structural safety. Input real verified properties before design.

### Example for unit checks — H-300x300x10x15

Idealized geometry *only*, neglecting radii:

| Property | Formula-derived quantity |
| --- | ---: |
| A | 0.011700 m² |
| I strong | 0.0001993275 m⁴ |
| I weak | 0.0000675225 m⁴ |
| calculated nominal mass at 7,850 kg/m³ | 91.845 kg/m |
| GO Factory older approximate kg/m | 94 kg/m |

These numbers are NOT a claim that this profile matches a manufacturer
catalog or that the member is safe.

## Integration flow

1. GO Factory v0.3.2-preview generates 3D members, stores stable section ID,
   Core version and catalog SHA in each member ext metadata, and retains its
   existing geometric and BOM algorithms.
2. GO anaStruct v0.5.7-preview reads the Section ID and verifies the version
   and hash when present. It no longer defaults an H/WF to an RC section.
3. User explicitly selects STRONG or WEAK in-plane axis and acknowledges
   nominal/unverified properties in a modal dialogue before importing a model.
4. GO anaStruct stores A, Iz, provenance, chosen axis and verified=False in
   its FEM Section. Pin/Fixed changes invalidate results.
5. Loads, combinations and releases are preserved when selecting an
   equivalent Factory frame station. Geometry/connectivity changes require
   confirmation before the edited model is replaced.

## Windows QA / release gates

GO Factory: run `RUN_GO_CORE_032_TESTS_WINDOWS.cmd`, then
`install_preview_032_windows.cmd` after closing IngeTrazo.

GO anaStruct: run `RUN_GO_CORE_057_TESTS_WINDOWS.cmd`, then
`install_preview_057_windows.cmd`; the existing verified v0.5.5 worker
may be reused. Test 3D overlays, Point/Line Loads, End Releases, Load
Combinations, Pin/Fixed support freshness, and save/reopen on IngeTrazo 0.5.9.

**The preview scripts have been authored, but real Windows GUI acceptance is
not yet demonstrated in this authoring session.** Keep both PRs as drafts
until user validation and licensed source data/engineering review are complete.
