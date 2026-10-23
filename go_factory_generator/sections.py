from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

@dataclass(frozen=True)
class SectionSpec:
    name: str
    family: str
    depth_m: float
    width_m: float
    web_m: float
    flange_m: float
    thickness_m: float
    unit_weight_kg_m: float
    material: str = "Steel"

# Starter library only. Keep values reviewable and easy to replace with a verified
# supplier/JIS/AISC database later. Geometry uses nominal dimensions; weight drives BOQ.
SECTION_LIBRARY: Dict[str, SectionSpec] = {
    "H-200x200x8x12": SectionSpec("H-200x200x8x12", "H", .200, .200, .008, .012, .0, 49.9),
    "H-250x250x9x14": SectionSpec("H-250x250x9x14", "H", .250, .250, .009, .014, .0, 72.4),
    "H-300x300x10x15": SectionSpec("H-300x300x10x15", "H", .300, .300, .010, .015, .0, 94.0),
    "H-350x350x12x19": SectionSpec("H-350x350x12x19", "H", .350, .350, .012, .019, .0, 137.0),
    "WF-250x125": SectionSpec("WF-250x125", "H", .250, .125, .006, .009, .0, 29.6),
    "WF-300x150": SectionSpec("WF-300x150", "H", .300, .150, .0065, .009, .0, 36.7),
    "C-100x50x20x2.3": SectionSpec("C-100x50x20x2.3", "C", .100, .050, .0, .0, .0023, 4.5),
    "C-150x65x20x2.3": SectionSpec("C-150x65x20x2.3", "C", .150, .065, .0, .0, .0023, 6.7),
    "Z-150x65x20x2.3": SectionSpec("Z-150x65x20x2.3", "Z", .150, .065, .0, .0, .0023, 6.7),
    "L-50x50x6": SectionSpec("L-50x50x6", "L", .050, .050, .0, .0, .006, 4.47),
    "L-65x65x6": SectionSpec("L-65x65x6", "L", .065, .065, .0, .0, .006, 5.91),
    "PIPE-48.6x3.2": SectionSpec("PIPE-48.6x3.2", "PIPE", .0486, .0486, .0, .0, .0032, 3.58),
    "PIPE-60.5x3.2": SectionSpec("PIPE-60.5x3.2", "PIPE", .0605, .0605, .0, .0, .0032, 4.52),
    "PL-400x400x20": SectionSpec("PL-400x400x20", "PLATE", .020, .400, .0, .0, .0, 0.0),
}

DEFAULT_SECTION_BY_ROLE = {
    "column": "H-300x300x10x15",
    "rafter": "WF-300x150",
    "truss": "L-65x65x6",
    "purlin": "Z-150x65x20x2.3",
    "girt": "C-150x65x20x2.3",
    "bracing": "L-50x50x6",
    "crane": "H-300x300x10x15",
    "mezz": "WF-300x150",
    "lean": "WF-250x125",
    "endwall": "C-150x65x20x2.3",
    "base": "PL-400x400x20",
}

def names_for_family(family: str) -> List[str]:
    return [k for k, s in SECTION_LIBRARY.items() if s.family == family]
