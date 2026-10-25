# GO Factory Generator for IngeTrazo

Parametric steel factory / warehouse generator for IngeTrazo.

## Screenshot
<img width="1898" height="1013" alt="Screenshot 2026-10-23 222615" src="https://github.com/user-attachments/assets/7f76e674-b4f2-40eb-b9c9-16139c7b64ad" />


## Status

**v0.3.1** — English-only Community patch based on the tested v0.3.0 release for IngeTrazo 0.5.9.

## Current capabilities

- Parametric factory geometry: width, length, bays, eave height and roof rise
- Portal frame / truss-oriented steel member generation
- Roof shapes: Gable, Mono-slope, Hip, Gambrel, Arched, Sawtooth and Cross Gable
- Columns, rafters, truss members, purlins, girts and bracing
- Optional centre columns, crane runway, mezzanine, lean-to and end-wall framing
- Group / Component generation using IngeTrazo containers
- Layers and per-category colors
- Expanded steel section library covering H/WF, C/Z, angles, RHS/SHS, flat/round bar, pipe and plate
- Metadata-based quantity takeoff with connection allowance, wastage and CSV export
- GO Factory toolbar: Create, Settings, Takeoff and Rebuild
- Undoable scene mutation through IngeTrazo history

## Installation

### Recommended: IngeTrazo Community Catalog

Once the extension is published in the IngeTrazo Community catalog:

1. Open IngeTrazo.
2. Open the Extensions manager.
3. Find **GO Factory Generator**.
4. Install it and restart IngeTrazo.

### Windows manual installer

For direct installation from this repository:

1. Download or clone this repository.
2. Close IngeTrazo completely.
3. Double-click `install_windows.cmd`.
4. Wait for `SUCCESS`.
5. Reopen IngeTrazo and look for the **GO Factory** toolbar.

The installer copies:

```text
go_factory_generator/
```

to:

```text
%APPDATA%\ingetrazo\plugins\go_factory_generator
```

If an older installation exists, it is backed up under:

```text
%APPDATA%\ingetrazo\go_factory_backups\
```

To remove the manually installed extension, close IngeTrazo and run:

```text
uninstall_windows.cmd
```

### Development / local test

You can also copy the `go_factory_generator` folder manually into:

```text
%APPDATA%\ingetrazo\plugins\go_factory_generator
```

and restart IngeTrazo.

For public Community installation, use the versioned ZIP from `dist/`; it contains exactly one plugin folder with `__init__.py`.

## Open Core direction

This repository is the Community core. Commercial / Professional modules may be developed separately and are not automatically covered by this repository's license.

## Safety / engineering scope

Generated geometry and quantities are modelling aids. Section data and structural behaviour must be independently verified before engineering, procurement or construction use.

## License

Apache License 2.0. See `LICENSE` and `NOTICE`.
