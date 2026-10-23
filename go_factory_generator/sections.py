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

# Starter library. Geometry uses nominal dimensions; weight drives BOQ.
# Unit weights are APPROXIMATE (JIS/AISC handbook values) and MUST be verified
# against a supplier catalogue before any procurement or structural use.
#
# Field convention per family:
#   H / WF  : depth=section depth, width=flange width, web=web t, flange=flange t
#   C / Z   : depth=depth, width=flange(lip side) width, thickness=plate t
#   L / LU  : depth=long(or single) leg, width=short leg, thickness=t (LU = unequal)
#   RHS/SHS : depth=outer depth, width=outer width, thickness=wall t
#   PIPE    : width=outer diameter, thickness=wall t
#   FB      : width=bar width, thickness=t
#   RB      : width=diameter
#   PLATE   : depth=plate t, width=plate width
SECTION_LIBRARY: Dict[str, SectionSpec] = {
    # ---- H / wide-flange columns & beams (JIS H) ----
    "H-100x100x6x8":   SectionSpec("H-100x100x6x8",   "H", .100, .100, .006, .008, .0, 16.5),
    "H-125x125x6.5x9": SectionSpec("H-125x125x6.5x9", "H", .125, .125, .0065, .009, .0, 23.6),
    "H-150x150x7x10":  SectionSpec("H-150x150x7x10",  "H", .150, .150, .007, .010, .0, 31.3),
    "H-175x175x7.5x11":SectionSpec("H-175x175x7.5x11","H", .175, .175, .0075, .011, .0, 40.9),
    "H-200x200x8x12":  SectionSpec("H-200x200x8x12",  "H", .200, .200, .008, .012, .0, 49.9),
    "H-250x250x9x14":  SectionSpec("H-250x250x9x14",  "H", .250, .250, .009, .014, .0, 72.4),
    "H-300x300x10x15": SectionSpec("H-300x300x10x15", "H", .300, .300, .010, .015, .0, 94.0),
    "H-350x350x12x19": SectionSpec("H-350x350x12x19", "H", .350, .350, .012, .019, .0, 137.0),
    "H-400x400x13x21": SectionSpec("H-400x400x13x21", "H", .400, .400, .013, .021, .0, 172.0),
    "H-414x405x18x28": SectionSpec("H-414x405x18x28", "H", .414, .405, .018, .028, .0, 233.0),
    "H-400x300x10x16": SectionSpec("H-400x300x10x16", "H", .400, .300, .010, .016, .0, 107.0),
    "H-500x300x11x18": SectionSpec("H-500x300x11x18", "H", .500, .300, .011, .018, .0, 128.0),
    "H-588x300x12x20": SectionSpec("H-588x300x12x20", "H", .588, .300, .012, .020, .0, 137.0),
    "H-600x300x12x20": SectionSpec("H-600x300x12x20", "H", .600, .300, .012, .020, .0, 149.0),
    # ---- WF light wide flange (beams/rafters) ----
    "WF-100x50":   SectionSpec("WF-100x50",   "H", .100, .050, .0060, .0070, .0, 14.5),
    "WF-125x60":   SectionSpec("WF-125x60",   "H", .125, .060, .0065, .0080, .0, 19.7),
    "WF-150x75":   SectionSpec("WF-150x75",   "H", .150, .075, .0050, .0070, .0, 16.7),
    "WF-175x90":   SectionSpec("WF-175x90",   "H", .175, .090, .0050, .0080, .0, 21.9),
    "WF-198x99":   SectionSpec("WF-198x99",   "H", .198, .099, .0045, .0070, .0, 17.9),
    "WF-250x125":  SectionSpec("WF-250x125",  "H", .250, .125, .0060, .0090, .0, 29.6),
    "WF-298x149":  SectionSpec("WF-298x149",  "H", .298, .149, .0045, .0055, .0, 28.5),
    "WF-300x150":  SectionSpec("WF-300x150",  "H", .300, .150, .0065, .0090, .0, 36.7),
    "WF-346x174":  SectionSpec("WF-346x174",  "H", .346, .174, .0060, .0090, .0, 41.4),
    "WF-396x199":  SectionSpec("WF-396x199",  "H", .396, .199, .0070, .0110, .0, 56.4),
    "WF-498x199":  SectionSpec("WF-498x199",  "H", .498, .199, .0090, .0140, .0, 79.5),
    "WF-588x300":  SectionSpec("WF-588x300",  "H", .588, .300, .0120, .0200, .0, 137.0),
    # ---- C / Z cold-formed lipped channels (girts, purlins) ----
    "C-100x50x20x2.3": SectionSpec("C-100x50x20x2.3", "C", .100, .050, .0, .0, .0023, 4.5),
    "C-120x50x20x2.3": SectionSpec("C-120x50x20x2.3", "C", .120, .050, .0, .0, .0023, 5.4),
    "C-150x65x20x2.3": SectionSpec("C-150x65x20x2.3", "C", .150, .065, .0, .0, .0023, 6.7),
    "C-200x75x25x3.0": SectionSpec("C-200x75x25x3.0", "C", .200, .075, .0, .0, .0030, 9.5),
    "C-250x80x25x3.2": SectionSpec("C-250x80x25x3.2", "C", .250, .080, .0, .0, .0032, 11.5),
    "Z-150x65x20x2.3": SectionSpec("Z-150x65x20x2.3", "Z", .150, .065, .0, .0, .0023, 6.7),
    "Z-175x70x20x2.3": SectionSpec("Z-175x70x20x2.3", "Z", .175, .070, .0, .0, .0023, 7.2),
    "Z-200x75x25x2.5": SectionSpec("Z-200x75x25x2.5", "Z", .200, .075, .0, .0, .0025, 9.0),
    "Z-250x80x25x3.0": SectionSpec("Z-250x80x25x3.0", "Z", .250, .080, .0, .0, .0030, 11.0),
    # ---- L equal angles (bracing, secondary) ----
    "L-25x25x3":   SectionSpec("L-25x25x3",   "L", .025, .025, .0, .0, .003, 1.12),
    "L-30x30x3":   SectionSpec("L-30x30x3",   "L", .030, .030, .0, .0, .003, 1.37),
    "L-40x40x4":   SectionSpec("L-40x40x4",   "L", .040, .040, .0, .0, .004, 2.42),
    "L-50x50x5":   SectionSpec("L-50x50x5",   "L", .050, .050, .0, .0, .005, 3.77),
    "L-50x50x6":   SectionSpec("L-50x50x6",   "L", .050, .050, .0, .0, .006, 4.47),
    "L-63x63x6":   SectionSpec("L-63x63x6",   "L", .063, .063, .0, .0, .006, 5.79),
    "L-65x65x6":   SectionSpec("L-65x65x6",   "L", .065, .065, .0, .0, .006, 5.91),
    "L-75x75x6":   SectionSpec("L-75x75x6",   "L", .075, .075, .0, .0, .006, 6.89),
    "L-75x75x8":   SectionSpec("L-75x75x8",   "L", .075, .075, .0, .0, .008, 9.03),
    "L-100x100x8": SectionSpec("L-100x100x8", "L", .100, .100, .0, .0, .008, 12.2),
    "L-100x100x10":SectionSpec("L-100x100x10","L", .100, .100, .0, .0, .010, 15.1),
    "L-125x125x10":SectionSpec("L-125x125x10","L", .125, .125, .0, .0, .010, 19.1),
    "L-150x150x12":SectionSpec("L-150x150x12","L", .150, .150, .0, .0, .012, 27.4),
    # ---- LU unequal angles ----
    "LU-100x63x8":  SectionSpec("LU-100x63x8",  "LU", .100, .063, .0, .0, .008, 9.9),
    "LU-125x75x10": SectionSpec("LU-125x75x10", "LU", .125, .075, .0, .0, .010, 15.3),
    "LU-150x90x12": SectionSpec("LU-150x90x12", "LU", .150, .090, .0, .0, .012, 22.0),
    # ---- RHS / SHS hollow structural sections ----
    "RHS-100x50x5":   SectionSpec("RHS-100x50x5",   "RHS", .100, .050, .0, .0, .005, 10.8),
    "RHS-150x100x6":  SectionSpec("RHS-150x100x6",  "RHS", .150, .100, .0, .0, .006, 21.4),
    "RHS-200x100x8":  SectionSpec("RHS-200x100x8",  "RHS", .200, .100, .0, .0, .008, 34.4),
    "RHS-250x150x8":  SectionSpec("RHS-250x150x8",  "RHS", .250, .150, .0, .0, .008, 45.5),
    "SHS-50x50x3":    SectionSpec("SHS-50x50x3",    "SHS", .050, .050, .0, .0, .003, 4.37),
    "SHS-75x75x4":    SectionSpec("SHS-75x75x4",    "SHS", .075, .075, .0, .0, .004, 8.79),
    "SHS-100x100x5":  SectionSpec("SHS-100x100x5",  "SHS", .100, .100, .0, .0, .005, 14.5),
    "SHS-150x150x8":  SectionSpec("SHS-150x150x8",  "SHS", .150, .150, .0, .0, .008, 34.4),
    "SHS-200x200x10": SectionSpec("SHS-200x200x10", "SHS", .200, .200, .0, .0, .010, 58.8),
    # ---- Round / square hollow pipe ----
    "PIPE-48.6x3.2":  SectionSpec("PIPE-48.6x3.2",  "PIPE", .0486, .0486, .0, .0, .0032, 3.58),
    "PIPE-60.5x3.2":  SectionSpec("PIPE-60.5x3.2",  "PIPE", .0605, .0605, .0, .0, .0032, 4.52),
    "PIPE-76.3x3.6":  SectionSpec("PIPE-76.3x3.6",  "PIPE", .0763, .0763, .0, .0, .0036, 6.46),
    "PIPE-89.1x4.2":  SectionSpec("PIPE-89.1x4.2",  "PIPE", .0891, .0891, .0, .0, .0042, 8.80),
    "PIPE-114.3x5.0": SectionSpec("PIPE-114.3x5.0", "PIPE", .1143, .1143, .0, .0, .0050, 13.5),
    # ---- Flat bar / round bar ----
    "FB-50x6":  SectionSpec("FB-50x6",  "FB", .006, .050, .0, .0, .006, 2.36),
    "FB-75x8":  SectionSpec("FB-75x8",  "FB", .008, .075, .0, .0, .008, 4.71),
    "FB-100x10":SectionSpec("FB-100x10","FB", .010, .100, .0, .0, .010, 7.85),
    "RB-20": SectionSpec("RB-20", "RB", .020, .020, .0, .0, .0, 2.47),
    "RB-25": SectionSpec("RB-25", "RB", .025, .025, .0, .0, .0, 3.85),
    "RB-32": SectionSpec("RB-32", "RB", .032, .032, .0, .0, .0, 6.31),
    # ---- Base / connection plates ----
    "PL-300x300x16": SectionSpec("PL-300x300x16", "PLATE", .016, .300, .0, .0, .0, 0.0),
    "PL-400x400x20": SectionSpec("PL-400x400x20", "PLATE", .020, .400, .0, .0, .0, 0.0),
    "PL-500x500x25": SectionSpec("PL-500x500x25", "PLATE", .025, .500, .0, .0, .0, 0.0),
    "PL-600x600x30": SectionSpec("PL-600x600x30", "PLATE", .030, .600, .0, .0, .0, 0.0),
}

DEFAULT_SECTION_BY_ROLE = {
    "column": "H-300x300x10x15",
    "rafter": "WF-300x150",
    "truss": "L-65x65x6",
    "truss_top": "WF-300x150",
    "truss_bottom": "WF-300x150",
    "truss_web": "L-65x65x6",
    "purlin": "Z-150x65x20x2.3",
    "girt": "C-150x65x20x2.3",
    "bracing": "L-50x50x6",
    "crane": "H-300x300x10x15",
    "mezz": "WF-300x150",
    "lean": "WF-250x125",
    "endwall": "C-150x65x20x2.3",
}

def names_for_family(family: str) -> List[str]:
    return [k for k, s in SECTION_LIBRARY.items() if s.family == family]
