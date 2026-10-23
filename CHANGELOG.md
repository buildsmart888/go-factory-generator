# Changelog

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
