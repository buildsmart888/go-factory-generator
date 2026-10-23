PLUGIN_KEY = "go_factory_generator"
PLUGIN_VERSION = "0.2.3"

LAYER_COLORS = {
    "GO-FAC-COLUMN": (0.10, 0.35, 0.90),
    "GO-FAC-RAFTER": (0.08, 0.48, 0.20),
    "GO-FAC-TRUSS": (0.95, 0.78, 0.08),
    "GO-FAC-PURLIN": (0.08, 0.25, 0.12),
    "GO-FAC-GIRT": (0.12, 0.32, 0.40),
    "GO-FAC-BRACING": (0.55, 0.34, 0.12),
    "GO-FAC-BASE": (0.35, 0.35, 0.38),
    "GO-FAC-CRANE": (0.55, 0.18, 0.65),
    "GO-FAC-MEZZ": (0.12, 0.55, 0.75),
    "GO-FAC-ENDWALL": (0.55, 0.55, 0.20),
    "GO-FAC-LEAN": (0.15, 0.55, 0.45),
}

CATEGORY_TO_LAYER = {
    "Column": "GO-FAC-COLUMN",
    "Rafter": "GO-FAC-RAFTER",
    "Truss": "GO-FAC-TRUSS",
    "Purlin": "GO-FAC-PURLIN",
    "Girt": "GO-FAC-GIRT",
    "Bracing": "GO-FAC-BRACING",
    "Base Plate": "GO-FAC-BASE",
    "Crane Beam": "GO-FAC-CRANE",
    "Mezzanine Beam": "GO-FAC-MEZZ",
    "End-wall Member": "GO-FAC-ENDWALL",
    "Lean-to Member": "GO-FAC-LEAN",
}
