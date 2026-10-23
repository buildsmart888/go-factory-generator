from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Tuple

@dataclass
class MemberRecord:
    uid: str
    project: str
    mark: str
    category: str
    layer: str
    section: str
    family: str
    start: Tuple[float,float,float]
    end: Tuple[float,float,float]
    length_m: float
    unit_weight_kg_m: float
    ifc_class: str
    container: str

    @property
    def weight_kg(self):
        return self.length_m * self.unit_weight_kg_m

    def to_dict(self):
        return asdict(self)
