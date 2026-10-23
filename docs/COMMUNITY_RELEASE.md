# Community release checklist

1. Runtime acceptance on the target IngeTrazo version.
2. Confirm toolbar appears after restart.
3. Confirm Create opens without traceback.
4. Generate a default factory and verify Groups/Components and layers.
5. Verify Settings opens and colors change.
6. Verify Takeoff opens from an existing model after the generator dialog is closed.
7. Verify Rebuild is one undoable operation.
8. Build the Community ZIP containing exactly one `go_factory_generator/` folder.
9. Compute SHA-256 of the exact ZIP.
10. Create an immutable Git tag/release or use an immutable commit SHA.
11. Point `extensions/go_factory_generator.toml` at the exact versioned asset.
12. Open a PR to `ingelibre/ingetrazo-extensions`.
