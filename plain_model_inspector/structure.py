from enum import Enum
from pydantic import BaseModel
from typing import Protocol, Optional, List


class BranchID(BaseModel):
    id: str


class BranchStructureDescription(BaseModel):
    name: str
    branch_id: Optional[BranchID]
    chainage: Optional[float]
    number_of_coordinates: Optional[int] # Can we have optional constrained values?
    x_coordinates: Optional[List[float]]
    y_coordinates: Optional[List[float]]


class StructureType(Enum):
    Weir = "weir"
    

class Structure(Protocol):
    structure_type: StructureType
    branch_description: BranchStructureDescription


class AllowedFlowDirection(Enum):
    BOTH = "both"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NONE = "none"


class Weir(BaseModel):
    structure_type: StructureType
    branch_description: BranchStructureDescription
    allowed_flow_direction: AllowedFlowDirection
    crest_level: float
    crest_width: float
    correction_coefficient: float = 1.0
    use_velocity_height: bool = True
    