# Changelog

## 0.3.1 - 2026-10-25

- Converted all remaining GO Factory toolbar labels and tooltips to English for international Community distribution.
- Standardized the public extension UI and messaging as English-only.
- Corrected the package SPDX identifier to Apache-2.0 so source metadata matches the repository and Community catalog license.
- No modelling, geometry, analysis or takeoff algorithms were intentionally changed in this patch.

## 0.3.0 - 2026-10-24

- Roof shapes: added Hip (hip/valley jack rafters + purlins on all 4 faces), Gambrel, Arched (barrel vault), Sawtooth (monitor) and Cross Gable (true 45° valleys with trimmed jack rafters).
- Truss system (new `truss.py`): 14 chord-driven web types — Pratt, Howe, Warren, Fink, Flat, Sloping, Dual-pitch, Curved, Under-camber, Camber, Scissor, Bowstring, North-light, Multi-span — plus main truss, sub-trusses and roof bracing (top-chord X/Staggered, bottom-chord, edge/vertical).
- Sections: expanded library to ~75 sizes across 11 families (H/WF JIS series, C/Z, equal & unequal angles, RHS/SHS hollow, flat/round bar, pipe, plate); per-member roles truss_top / truss_bottom / truss_web.
- Consistency: purlins, columns, girts and bracing now follow the actual truss chords (`truss_nodes`) instead of the nominal roof profile.
- Takeoff: connection-allowance and wastage percentages, extra BOQ columns and CSV export.
- UI: live truss preview (elevation + plan bracing, part labels, dimensions, layer legend), scrollable tabs, larger fonts, slope-by-angle, presets save/load (JSON).
- New layers/categories for hip, gable wall, skylight, sub-truss and roof bracing.
- Targeted IngeTrazo 0.5.9 Extension API v2.

## 0.2.3 - 2026-10-23

- Fixed Sections-tab initialization that could raise `AttributeError: 'NoneType' object has no attribute 'layout'`.
- Added GO Factory toolbar with Create, Settings, Takeoff and Rebuild actions.
- Added scene-based takeoff reopening from stored GO Factory metadata.
- Normalized plugin metadata to version 0.2.3.
- Targeted IngeTrazo 0.5.9 plugin API pattern using `setup(app)`.
- Runtime acceptance passed on IngeTrazo 0.5.9: toolbar, generation, settings, takeoff and rebuild.

## 0.2.2

- Switched primary extension entry to `setup(app)`.
- Added Windows installer pattern for local testing.

## 0.2.x

- Introduced package architecture, Group/Component model, section library, colors, layers, portal/truss options, crane/mezzanine/lean-to/end-wall features and BOQ metadata.
