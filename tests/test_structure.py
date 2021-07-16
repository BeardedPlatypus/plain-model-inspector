from os import name
from plain_model_inspector.structure import *

def test_BranchID_constructor():
    id_value = "some_branch_id"
    branch_id = BranchID(id = id_value)

    assert branch_id.id == id_value


def assert_structure(structure: Structure, 
                     structure_type: StructureType,
		     branch_name: str):
    assert structure.structure_type == structure_type
    assert structure.branch_description.name == branch_name


def test_weir_is_a_structure():
    description = BranchStructureDescription(name="someName")
    weir = Weir(structure_type=StructureType.Weir,
                branch_description=description, 
		allowed_flow_direction=AllowedFlowDirection.NONE,
		crest_level=0.0, 
		crest_width=0.0)

    assert_structure(weir, StructureType.Weir, "someName")
