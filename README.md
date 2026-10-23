# GO Factory Generator for IngeTrazo

Parametric steel factory / warehouse generator for IngeTrazo.

## Status

**v0.2.3 Release Candidate** — targeted at IngeTrazo 0.5.9. Public catalog release should follow runtime acceptance in IngeTrazo.

## Current capabilities

- Parametric factory geometry: width, length, bays, eave height and roof rise
- Portal frame / truss-oriented steel member generation
- Gable and mono-slope roof options
- Columns, rafters, truss members, purlins, girts and bracing
- Optional centre columns, crane runway, mezzanine, lean-to and end-wall framing
- Group / Component generation using IngeTrazo containers
- Layers and per-category colors
- Starter steel section library (H/WF/C/Z/Angle/Pipe/Plate)
- Quantity takeoff from extension metadata
- GO Factory toolbar: Create, Settings, Takeoff and Rebuild
- Undoable scene mutation through IngeTrazo history

## Installation (development / local test)

Copy the `go_factory_generator` folder into the per-user IngeTrazo plugins directory and restart IngeTrazo.

Windows:

```text
%APPDATA%\ingetrazo\plugins\go_factory_generator
```

For public Community installation, use the versioned ZIP from `dist/`; it contains exactly one plugin folder with `__init__.py`.

## Open Core direction

This repository is the Community core. Commercial / Professional modules may be developed separately and are not automatically covered by this repository's license.

## Safety / engineering scope

Generated geometry and quantities are modelling aids. Section data and structural behaviour must be independently verified before engineering, procurement or construction use.

## License

Apache License 2.0. See `LICENSE` and `NOTICE`.
