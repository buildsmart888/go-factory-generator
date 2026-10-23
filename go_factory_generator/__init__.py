# SPDX-License-Identifier: GPL-3.0-or-later
"""GO Factory Generator v0.2.3 for IngeTrazo 0.5.9+."""
from __future__ import annotations
import logging

log = logging.getLogger("ingetrazo.plugins.go_factory_generator")
PLUGIN_KEY = "go_factory_generator"
PLUGIN_VERSION = "0.2.3"


def _register_browser_metadata(app):
    add_kind = getattr(app, "add_outliner_kind", None)
    if not callable(add_kind):
        return

    def kind(group):
        meta = (getattr(group, "ext", None) or {}).get(PLUGIN_KEY)
        if not meta:
            return None
        return {
            "type": "GO Steel Member",
            "props": [
                ("Mark", str(meta.get("mark", ""))),
                ("Section", str(meta.get("section", ""))),
                ("Category", str(meta.get("category", ""))),
                ("Length", f"{float(meta.get('length_m', 0.0)):.3f} m"),
                ("Weight", f"{float(meta.get('weight_kg', 0.0)):.1f} kg"),
                ("Container", str(meta.get("container", ""))),
                ("Project", str(meta.get("project", ""))),
            ],
        }
    try:
        add_kind(kind)
    except Exception:
        log.exception("GO Factory Browser metadata integration failed")


def setup(app):
    if getattr(app, "api_version", 0) < 2:
        raise RuntimeError("GO Factory Generator v0.2.3 requires Extension API_VERSION >= 2")
    from .toolbar import install_toolbar
    install_toolbar(app)
    _register_browser_metadata(app)
    log.info("GO Factory Generator v0.2.3 loaded")
